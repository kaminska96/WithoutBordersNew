from django.urls import path
from . import views
from django.urls import path
from .views import Index
from .views import create_warehouse


urlpatterns = [
    path('signup/', views.signup, name='signup'),
    path('login/', views.login, name='login'),
    path('main/', views.main, name='main'),
    path('main2/', views.main2, name='main2'),
    path('main3/', views.main3, name='main3'),
    path('warehouses/<int:warehouse_id>/', views.updateWarehouse, name='update_warehouse'),
    path('', Index.as_view(), name='index'),
    path('create-warehouse/', create_warehouse, name='create_warehouse'),
]
