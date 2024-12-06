from django.contrib import admin
from django.urls import path
from . import views

# urlpatterns = [
#     path('',  views.lobby),
# ]

urlpatterns = [
    path("signup/", views.user_signup, name="signup"),
    path("login/", views.user_login, name="login"),
    path("", views.chat, name="chat"),
    path("logout/", views.user_logout, name="logout"),
]