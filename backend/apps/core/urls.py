from django.urls import path

from . import views

urlpatterns = [
    path("health/", views.HealthView.as_view(), name="health"),
    path("demo/accounts/", views.DemoAccountsView.as_view(), name="demo-accounts"),
]
