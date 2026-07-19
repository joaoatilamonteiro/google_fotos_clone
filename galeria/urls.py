from django.urls import path

from . import views

urlpatterns = [
    path("", views.galeria_home, name="galeria_home")
]