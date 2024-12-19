from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
    path("signup/", views.user_signup, name="signup"),
    path("login/", views.user_login, name="login"),
    path("", views.home, name="chat"),
    path("create-group/", views.create_group, name="create-group"), 
    path("room/<str:room_name>/", views.room, name="room_with_name"),
    path("group/<str:group_name>/", views.group, name="group_with_name"),
    path("logout/", views.user_logout, name="logout"),
]