import uuid
from datetime import datetime

from django.contrib.auth.models import AbstractUser
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db import models
from pydash import get
from rest_framework.authtoken.models import Token

from core.common.mixins import SourceContainerMixin
from core.common.models import BaseModel, CommonLogoModel
from core.common.tasks import send_user_verification_email, send_user_reset_password_email
from core.common.utils import web_url
from core.users.constants import AUTH_GROUPS
from .constants import USER_OBJECT_TYPE
from ..common.checksums import ChecksumModel


class UserProfile(AbstractUser, BaseModel, CommonLogoModel, SourceContainerMixin, ChecksumModel):
    class Meta:
        db_table = 'user_profiles'
        swappable = 'AUTH_USER_MODEL'
        indexes = [
                      models.Index(fields=['uri']),
                      models.Index(fields=['public_access']),
                  ] + BaseModel.Meta.indexes

    OBJECT_TYPE = USER_OBJECT_TYPE
    first_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    organizations = models.ManyToManyField('orgs.Organization', related_name='members')
    company = models.TextField(null=True, blank=True)
    location = models.TextField(null=True, blank=True)
    preferred_locale = models.TextField(null=True, blank=True)
    website = models.TextField(null=True, blank=True)
    verified = models.BooleanField(default=True)
    verification_token = models.TextField(null=True, blank=True)
    deactivated_at = models.DateTimeField(null=True, blank=True)
    mnemonic_attr = 'username'

    es_fields = {
        'username': {'sortable': False, 'filterable': True, 'exact': True},
        '_username': {'sortable': True, 'filterable': False, 'exact': False},
        'name': {'sortable': False, 'filterable': True, 'exact': True},
        '_name': {'sortable': True, 'filterable': False, 'exact': False},
        'date_joined': {'sortable': True, 'default': 'asc', 'filterable': False},
        'updated_by': {'sortable': False, 'filterable': False, 'facet': True},
        'company': {'sortable': True, 'filterable': True, 'exact': True},
        'location': {'sortable': True, 'filterable': True, 'exact': True},
        'is_superuser': {'sortable': False, 'filterable': True, 'exact': False, 'facet': True},
        'is_staff': {'sortable': False, 'filterable': False, 'exact': False, 'facet': True},
        'is_admin': {'sortable': False, 'filterable': False, 'exact': False, 'facet': True}
    }

    STANDARD_CHECKSUM_INCLUSIONS = [
        'first_name', 'last_name', 'username', 'company', 'location', 'website', 'preferred_locale', 'extras']
    SMART_CHECKSUM_INCLUSIONS = [
        'first_name', 'last_name', 'username', 'company', 'location', 'website', 'is_active']

    def get_standard_checksum_fields(self):
        return self.get_standard_checksum_fields_for_resource(self)

    def get_smart_checksum_fields(self):
        return self.get_smart_checksum_fields_for_resource(self)

    @staticmethod
    def get_standard_checksum_fields_for_resource(data):
        return {
            'first_name': get(data, 'first_name'),
            'last_name': get(data, 'last_name'),
            'username': get(data, 'username'),
            'company': get(data, 'company'),
            'location': get(data, 'location'),
            'website': get(data, 'website'),
            'preferred_locale': get(data, 'preferred_locale'),
            'extras': get(data, 'extras')
        }

    @staticmethod
    def get_smart_checksum_fields_for_resource(data):
        return {
            'first_name': get(data, 'first_name'),
            'last_name': get(data, 'last_name'),
            'username': get(data, 'username'),
            'company': get(data, 'company'),
            'location': get(data, 'location'),
            'is_active': get(data, 'is_active')
        }

    def calculate_uri(self):
        return f"/users/{self.username}/"

    @staticmethod
    def get_search_document():
        from core.users.documents import UserProfileDocument
        return UserProfileDocument

    @property
    def status(self):
        if not self.is_active:
            return 'deactivated'
        if not self.verified:
            return 'verification_pending' if self.verification_token else 'unverified'

        return 'verified'

    @property
    def user(self):
        return self.username

    @property
    def name(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def full_name(self):
        return self.name

    @property
    def mnemonic(self):
        return self.username

    @staticmethod
    def get_url_kwarg():
        return 'user'

    @property
    def organizations_url(self):
        return f"/users/{self.mnemonic}/orgs/"

    def update_password(self, password=None, hashed_password=None):
        if not password and not hashed_password:
            return None

        if password:
            try:
                validate_password(password)
                self.set_password(password)
            except ValidationError as ex:
                return {'errors': ex.messages}
        elif hashed_password:
            self.password = hashed_password

        if self.verification_token:
            self.verification_token = None
        self.save()
        self.refresh_token()
        return None

    def refresh_token(self):
        self.__delete_token()
        self.__create_token()

    def get_token(self):
        token = Token.objects.filter(user_id=self.id).first() or self.__create_token()
        return token.key

    def set_token(self, token):
        self.__delete_token()
        Token.objects.create(user=self, key=token)

    def is_admin_for(self, concept_container):  # pragma: no cover
        parent_id = concept_container.parent_id
        return parent_id == self.id or self.organizations.filter(id=parent_id).exists()

    def __create_token(self):
        return Token.objects.create(user=self)

    def __delete_token(self):
        return Token.objects.filter(user=self).delete()

    @property
    def orgs_count(self):
        return self.organizations.count()

    @property
    def owned_orgs_count(self):
        return self.organizations.filter(created_by=self).count()

    def send_verification_email(self):
        return send_user_verification_email.delay(self.id)

    def send_reset_password_email(self):
        return send_user_reset_password_email.delay(self.id)

    @property
    def email_verification_url(self):
        return f"{web_url()}/#/accounts/{self.username}/verify/{self.verification_token}/"

    @property
    def reset_password_url(self):
        return f"{web_url()}/#/accounts/{self.username}/password/reset/{self.verification_token}/"

    def mark_verified(self, token, force=False):
        if self.verified:
            return True

        if token == self.verification_token or force:
            self.verified = True
            self.verification_token = None
            self.deactivated_at = None
            self.save()
            return True

        return False

    @staticmethod
    def is_valid_auth_group(*names):
        return all(name in AUTH_GROUPS for name in names)

    @property
    def auth_groups(self):
        return self.groups.values_list('name', flat=True)

    @property
    def auth_headers(self):
        return {'Authorization': f'Token {self.get_token()}'}

    def deactivate(self):
        self.is_active = False
        self.verified = False
        self.verification_token = None
        self.deactivated_at = datetime.now()
        self.__delete_token()
        self.save()
        self.set_checksums()

    def verify(self):
        self.is_active = True
        self.verified = False
        self.verification_token = uuid.uuid4()

        self.save()
        self.token = self.get_token()
        self.send_verification_email()

    def soft_delete(self):
        self.deactivate()

    def undelete(self):
        self.verified = True
        self.verification_token = None
        self.deactivated_at = None
        self.is_active = True
        self.save()
        self.set_checksums()
