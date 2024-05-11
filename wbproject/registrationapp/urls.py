from django.urls import path
from . import views
from django.urls import path
from .views import Index, get_order_details
from .views import create_warehouse
from .views import get_warehouse_details
from .views import create_order
from django.contrib.auth import views as auth_views


urlpatterns = [
    path('signup/', views.signup, name='signup'),
    path('login/', views.login, name='login'),
    path('main/', views.main, name='main'),
    path('dostavka_now/', views.dostavka_now, name='dostavka_now'),
    path('dostavka_comp/', views.dostavka_comp, name='dostavka_comp'),
    path('main2/', views.main2, name='main2'),
    path('main3/', views.main3, name='main3'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('warehouses/<int:warehouse_id>/', views.updateWarehouse, name='update_warehouse'),
    path('', Index.as_view(), name='index'),
    path('create-warehouse/', create_warehouse, name='create_warehouse'),
    path('api/warehouse/<int:warehouse_id>/', get_warehouse_details, name='warehouse_details'),
    path('create-order/', create_order, name='create_order'),
    path('api/order/<int:order_id>/', get_order_details, name='order_details'),
]
