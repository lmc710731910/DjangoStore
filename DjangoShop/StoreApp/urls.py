from django.urls import path,re_path
from StoreApp.views import *


urlpatterns = [
    path('register/',register),
    path('login/', login),
    path('index/', index),
    re_path('^$', index),

]