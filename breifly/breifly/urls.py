from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from django.conf.urls.i18n import i18n_patterns
import breiflyplatform.views as views

# Base URL patterns
urlpatterns = [
    path('i18n/', include('django.conf.urls.i18n')),  # Language switching

]

# Language-aware patterns
urlpatterns += i18n_patterns(
    path('home/', views.landing_page, name='home'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout_view'),
    path('settings/', views.get_settings_view, name='get_settings_view'),
    path('settings/modify/', views.settings_modify_view, name='settings_modify_view'),
    path('settings/modify/account', views.account_modify_view, name='account_modify_view'),
    path('search/settings/modify/', views.modify_search_settings, name="modify_search_settings"),
    path('account/new/user/', views.finalise_new_user, name="finalise_new_user"),
    path('api/search/news/', views.get_news, name="get_news"),
    path('error/page/', views.error_page, name="error_page"),
    path('custom-admin/dashboard/', views.admin_dashboard, name="admin_dashboard"),
    path('custom-admin/dashboard/update/', views.admin_dashboard, name="admin_dashboard_update"),
    path('custom-admin/export/csv/', views.admin_dashboard_csv, name="admin_dashboard_csv"),
)

# Static file serving
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)