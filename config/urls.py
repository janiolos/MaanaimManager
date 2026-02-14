from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include

from apps.core import views as core_views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("login/", core_views.LoginDashboardView.as_view(), name="login"),
    path("", core_views.home, name="home"),
    path("", include("apps.finance.urls")),
    path("", include("apps.inventory.urls")),
    path("", include("apps.core.urls")),
    path("", include("apps.lodging.urls")),
    path("", include("apps.notifications.urls")),
    path("", include("django.contrib.auth.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
