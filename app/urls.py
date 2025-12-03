from django.urls import path
from . import views

urlpatterns = [
    path('moderate/', views.moderate_request),
]