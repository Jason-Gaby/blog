from django.conf import settings
from django.urls import include, path
from django.contrib import admin
from django.contrib.auth import urls as auth_urls
from wagtail.admin import urls as wagtailadmin_urls
from wagtail import urls as wagtail_urls
from wagtail.documents import urls as wagtaildocs_urls

from search import views as search_views
from users.views import CustomLoginView, CustomProfileView, CustomPasswordChangeView, CustomPasswordResetView, \
    CustomPasswordResetDoneView, CustomUserRegisterView, CustomLogoutView

urlpatterns = [
    path("django-admin/", admin.site.urls),
    path("admin/", include(wagtailadmin_urls)),
    path("documents/", include(wagtaildocs_urls)),
    path("account/login/", CustomLoginView.as_view(), name="login"),
    path("account/logout/", CustomLogoutView.as_view(), name="logout"),
    path("account/profile/", CustomProfileView.as_view(), name="profile"),
    path("account/password_change/", CustomPasswordChangeView.as_view(), name="password_change"),
    path("account/password_reset/", CustomPasswordResetView.as_view(), name="password_reset"),
    path("account/password_reset/done/", CustomPasswordResetDoneView.as_view(), name="password_reset_done"),
    path("account/register/", CustomUserRegisterView.as_view(), name="register"),
    # This block includes paths like 'password_reset/', 'reset/done/', etc.
    path("account/", include(auth_urls)), # NOTE: THIS MUST BE AFTER CUSTOM VIEWS!
    path("search/", search_views.search, name="search"),
    path("", include(wagtail_urls)),
]


if settings.DEBUG:
    from django.conf.urls.static import static
    from django.contrib.staticfiles.urls import staticfiles_urlpatterns

    # Serve static and media files from development server
    urlpatterns += staticfiles_urlpatterns()
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

urlpatterns = urlpatterns + [
    # For anything not caught by a more specific rule above, hand over to
    # Wagtail's page serving mechanism. This should be the last pattern in
    # the list:
    path("", include(wagtail_urls)),
    # Alternatively, if you want Wagtail pages to be served from a subpath
    # of your site, rather than the site root:
    #    path("pages/", include(wagtail_urls)),
]
