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
    path('planned_orders/', views.planned_orders, name='planned_orders'),
    path('orders_on_the_way/', views.orders_on_the_way, name='orders_on_the_way'),
    path('completed_orders/', views.completed_orders, name='completed_orders'),
    path('creating_order/', views.creating_order, name='creating_order'),
    path('warehouses/', views.warehouses, name='warehouses'),
    path('calendar/', views.calendar, name='calendar'),
    # path('import_warehouse_goods/', views.import_warehouse_goods, name='import_warehouse_goods'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('', Index.as_view(), name='withoutborders'),
    path('create-warehouse/', create_warehouse, name='create_warehouse'),
    path('delete_product/<int:product_id>/', views.delete_product, name='delete_product'),
    path('delete_vehicle/<int:vehicle_id>/', views.delete_vehicle, name='delete_vehicle'),
    path('api/warehouse/<int:warehouse_id>/', get_warehouse_details, name='warehouse_details'),
    path('update_warehouse/<int:warehouse_id>/', views.update_warehouse, name='update_warehouse'),
    path('create-order/', create_order, name='create_order'),
    path('api/order/<int:order_id>/', get_order_details, name='order_details'),
    path('api/warehouses/<int:product_id>/', views.get_warehouse_by_product, name='get_warehouse_by_product'),
    path('api/vehicle/<int:warehouse_id>/', views.get_vehicle_by_warehouse, name='get_vehicle_by_warehouse'),
    path('api/order/<int:order_id>/update_status/', views.update_order_status, name='update_order_status'),
    path('delete_warehouse/<int:warehouse_id>/', views.delete_warehouse, name='delete_warehouse'),
    path('delete_order/<int:order_id>/', views.delete_order, name='delete_order'),
    path('api/search_orders/', views.search_orders, name='search_orders'),
]
