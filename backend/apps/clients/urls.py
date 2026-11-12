from django.urls import path

from . import views

urlpatterns = [
    path("clients/", views.ClientListView.as_view(), name="client-list"),
    path("clients/<int:pk>/", views.ClientDetailView.as_view(), name="client-detail"),
]
