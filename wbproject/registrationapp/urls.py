from django.urls import path
from . import views


urlpatterns = [
    path('signup/', views.signup, name='signup'),
    path('login/', views.login, name='login'),
    path('main/', views.main, name='main'),
    path('main2/', views.main2, name='main2'),
    path('main3/', views.main3, name='main3'),

]
