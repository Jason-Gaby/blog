from django.shortcuts import render
from django.contrib.auth.views import LoginView, LogoutView

# Create your views here.

class CustomLoginView(LoginView):
    pass

class CustomLogoutView(LogoutView):
    pass

