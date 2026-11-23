from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path
from django.views.i18n import JavaScriptCatalog, set_language
from . import views

urlpatterns = [
    path("language/", set_language, name="set_language"),
    path("translations.js", JavaScriptCatalog.as_view(domain="django"), name="javascript-catalog"),
    path("", views.home, name="home"),
    path("campagnes/<uuid:reference>/", views.detail, name="detail"),
    path("signup/", views.signup, name="signup"),
    path("wallet/", views.connect_wallet, name="connect-wallet"),
    path("campagnes/<uuid:reference>/publish/", views.publish_campaign, name="publish-campaign"),
    path("studio/", views.studio, name="studio"),
    path("connexion/", auth_views.LoginView.as_view(template_name="login.html"), name="login"),
    path("deconnexion/", auth_views.LogoutView.as_view(), name="logout"),
    path("installation/", views.setup, name="setup"),
    path("admin/", admin.site.urls),
]
