from django.urls import path, include
from .views import LoginApi, GetUserApi
from knox import views as knox_views

urlpatterns = [
    path("api/auth", include("knox.urls")),
    path("api/auth/login", LoginApi.as_view()),
    path("api/auth/user", GetUserApi.as_view()),
    path("api/auth/logout", knox_views.LogoutView.as_view()),
]