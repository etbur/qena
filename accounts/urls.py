from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('register/',  views.register_view, name='register'),
    path('login/',     views.login_view,    name='login'),
    path('logout/',    views.logout_view,   name='logout'),
    path('profile/',   views.profile_view,  name='profile'),
    path('redirect/',  views.role_redirect, name='role_redirect'),  # LOGIN_REDIRECT_URL target
]
