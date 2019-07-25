from django.urls import path,include
from BuyerApp.views import *


urlpatterns = [
    path("login/",login),
    path("logout/", logout),
    path("register/", register),
    path("index/", index),


]

urlpatterns+=[
    path("base/",base)
]