from django.urls import re_path, include, path

from core.common.constants import NAMESPACE_PATTERN
from core.orgs import views as org_views
from . import views
from ..repos.views import OrganizationRepoListView
from ..url_registry.views import OrganizationURLRegistryListView

urlpatterns = [
    re_path(r'^$', views.UserListView.as_view(), name='userprofile-list'),
    path('api-token/', views.TokenExchangeView.as_view(), name='user-oid-django-token-exchange'),
    path('oidc/code-exchange/', views.OIDCodeExchangeView.as_view(), name='user-oid-code-exchange'),
    path('login/', views.TokenAuthenticationView.as_view(), name='user-login'),
    path('logout/', views.OIDCLogoutView.as_view(), name='user-logout'),
    path('signup/', views.UserSignup.as_view(), name='user-signup'),
    re_path(
        r'^(?P<user>' + NAMESPACE_PATTERN + ')/$',
        views.UserDetailView.as_view(),
        name='userprofile-detail'
    ),
    path(
        '<str:user>/sso-migrate/',
        views.SSOMigrateView.as_view(),
        name='userprofile-sso-migrate'
    ),
    path(
        '<str:user>/verify/<str:verification_token>/',
        views.UserEmailVerificationView.as_view(),
        name='userprofile-email-verify'
    ),
    path(
        'password/reset/',
        views.UserPasswordResetView.as_view(),
        name='userprofile-email-verify'
    ),
    re_path(
        r'^(?P<user>' + NAMESPACE_PATTERN + ')/logo/$',
        views.UserLogoView.as_view(),
        name='userprofile-logo'
    ),
    re_path(
        r'^(?P<user>' + NAMESPACE_PATTERN + ')/reactivate/$',
        views.UserReactivateView.as_view(),
        name='userprofile-reactivate'
    ),
    re_path(
        r'^(?P<user>' + NAMESPACE_PATTERN + ')/staff/$',
        views.UserStaffToggleView.as_view(),
        name='userprofile-reactivate'
    ),
    re_path(
        r'^(?P<user>' + NAMESPACE_PATTERN + ')/orgs/$',
        org_views.OrganizationListView.as_view(),
        name='userprofile-orgs'
    ),
    re_path(
        r'^(?P<user>' + NAMESPACE_PATTERN + ')/extras/$',
        views.UserExtrasView.as_view(),
        name='user-extras'
    ),
    re_path(
        r'^(?P<user>' + NAMESPACE_PATTERN + ')/orgs/sources/$',
        org_views.OrganizationSourceListView.as_view(),
        name='userprofile-organization-source-list'
    ),
    re_path(
        r'^(?P<user>' + NAMESPACE_PATTERN + ')/orgs/collections/$',
        org_views.OrganizationCollectionListView.as_view(),
        name='userprofile-organization-collection-list'
    ),
    re_path(
        r'^(?P<user>' + NAMESPACE_PATTERN + ')/orgs/repos/$',
        OrganizationRepoListView.as_view(),
        name='userprofile-organization-repo-list',
    ),
    re_path(
        r'^(?P<user>' + NAMESPACE_PATTERN + ')/orgs/url-registry/$',
        OrganizationURLRegistryListView.as_view(),
        name='userprofile-organization-url-registry-list',
    ),
    re_path(
        r"^(?P<user>{pattern})/extras/(?P<extra>{pattern})/$".format(pattern=NAMESPACE_PATTERN),
        views.UserExtraRetrieveUpdateDestroyView.as_view(),
        name='user-extra'
    ),
    re_path(r'^(?P<user>' + NAMESPACE_PATTERN + ')/repos/', include('core.repos.urls')),
    re_path(r'^(?P<user>' + NAMESPACE_PATTERN + ')/url-registry/', include('core.url_registry.urls')),
    re_path(r'^(?P<user>' + NAMESPACE_PATTERN + ')/sources/', include('core.sources.urls')),
    #TODO: require FHIR subdomain
    re_path(r'^(?P<user>' + NAMESPACE_PATTERN + ')/CodeSystem/', include('core.code_systems.urls'),
            name='code_systems_urls'),
    re_path(r'^(?P<user>' + NAMESPACE_PATTERN + ')/ValueSet/', include('core.value_sets.urls'),
            name='value_sets_urls'),
    re_path(r'^(?P<user>' + NAMESPACE_PATTERN + ')/ConceptMap/', include('core.concept_maps.urls'),
            name='concept_maps_urls'),
    re_path(r'^(?P<user>' + NAMESPACE_PATTERN + ')/collections/', include('core.collections.urls')),
    re_path(r'^(?P<user>' + NAMESPACE_PATTERN + ')/pins/', include('core.pins.urls')),
]
