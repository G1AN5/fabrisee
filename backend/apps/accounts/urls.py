from django.urls import path

from . import views

urlpatterns = [
    path("csrf/", views.CsrfView.as_view(), name="auth-csrf"),
    path("login/", views.LoginView.as_view(), name="auth-login"),
    path("logout/", views.LogoutView.as_view(), name="auth-logout"),
    path("me/", views.MeView.as_view(), name="auth-me"),
    path("privacy-notice/", views.PrivacyNoticeView.as_view(), name="auth-privacy-notice"),
    path("privacy-ack/", views.PrivacyAcknowledgeView.as_view(), name="auth-privacy-ack"),
]
