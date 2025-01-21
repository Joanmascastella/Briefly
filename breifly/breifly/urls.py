"""
URL configuration for breifly project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path


from breiflyplatform.views import *
urlpatterns = [
    path("", landing_page),
    path("admin/", admin.site.urls),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('settings/', settings_view, name='settings'),
    path('settings/modify/', settings_changed, name='settings'),
    path('account/', account_view, name='account'),
    path('account/modify/', account_changed, name='account'),
    path('search/settings/modify/', modify_search_settings, name="search"),
    path('account/new/user/', finalise_new_user, name="user"),
    path('api/search/news/', get_news, name="news"),
    path('error/page/', error_page, name="error"),
    path('custom-admin/dashboard/', admin_dashboard, name="custom-admin"),
    path('custom-admin/dashboard/update/', admin_dashboard, name="custom-admin-users"),
    path('custom-admin/export/csv/', admin_dashboard_csv, name="custom-admin-csv"),
]
