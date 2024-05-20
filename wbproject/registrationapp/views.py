from django.shortcuts import render
from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from django.contrib import messages, auth
# from withoutborders.models import Profile
from django.contrib import auth
from django.http import JsonResponse
from .models import Order_product, Order_vehicle, Product, Vehicle, Warehouse
from django.views.decorators.csrf import csrf_exempt
import json
from django.shortcuts import redirect
from django.shortcuts import render
from django.views import View

# Create your views here.

class Index(View):
    def get(self, request):
        return render(request, 'registrationapp/index.html')

def signup(request):
    if request.method == 'POST':
        first_name = request.POST['first_name']
        last_name = request.POST['last_name']
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        password2 = request.POST['password2']

        if password == password2:
            if User.objects.filter(email=email).exists():
                messages.info(request, 'Email already exists!')
                return redirect('signup')
            elif User.objects.filter(username=username).exists():
                messages.info(request, 'Username already exists!')
                return redirect('signup')
            else:
                user = User.objects.create_user(first_name=first_name, last_name=last_name, username=username, email=email, password=password)
                user.save()

                user_model = User.objects.get(username=username)
                # new_profile = Profile.objects.create(user=user_model, id_user=user_model.id)
                # new_profile.save()
                
                # auth.login(request, user)
                return redirect('main')
        else:
            messages.info(request, 'Passwords do not match!')
            return redirect('signup')
    else:
        return render(request, 'registrationapp/registration.html')

def login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']

        user = auth.authenticate(username=username, password=password)

        if user is not None:
            auth.login(request, user)
            return redirect('main')
        else:
            messages.info(request, 'Invalid credentials')
            return redirect('login')
    else:
        return render(request, 'registrationapp/login.html')
    
def main(request):
    if not request.user.is_authenticated:
        return redirect('login')
    orders = Order.objects.filter(user=request.user)  # Fetch all orders
    context = {'orders': orders}
    return render(request, 'registrationapp/main.html', context)

def dostavka_now(request):
    if not request.user.is_authenticated:
        return redirect('login')
    orders = Order.objects.filter(user=request.user)  # Fetch all orders
    context = {'orders': orders}
    return render(request, 'registrationapp/dostavka_now.html', context)

def dostavka_comp(request):
    if not request.user.is_authenticated:
        return redirect('login')
    orders = Order.objects.filter(user=request.user)  # Fetch all orders
    context = {'orders': orders}
    return render(request, 'registrationapp/dostavka_comp.html', context)

def main2(request):
    if not request.user.is_authenticated:
        return redirect('login')

    # Fetch warehouses for the current user
    warehouses = Warehouse.objects.filter(user=request.user)

    # If there are no warehouses, display an empty list (optional)
    if not warehouses.exists():
        products = []
    else:
        # Use list comprehension to get product IDs from warehouses
        product_ids = [list(warehouse.product_set.all().values_list('id', flat=True)) for warehouse in warehouses]

        # Flatten the list of lists (if there are multiple warehouses)
        product_ids = sum(product_ids, [])

        # Fetch products based on the retrieved IDs (avoids duplicate entries)
        products = Product.objects.filter(id__in=product_ids).distinct()

    context = {'products': products}
    return render(request, 'registrationapp/main2.html', context)

def main3(request): 
    if not request.user.is_authenticated:
        return redirect('login')
    warehouses = Warehouse.objects.filter(user=request.user)  # Fetch all warehouses
    context = {'warehouses': warehouses}
    return render(request, 'registrationapp/main3.html', context)

from django.http import JsonResponse

def update_warehouse(request, warehouse_id):
    if request.method == 'PUT':  # Allowing only PUT requests
        try:
            warehouse = Warehouse.objects.get(id=warehouse_id)
            if request.content_type == 'application/json':
                data = json.loads(request.body)
                updated_fields = {}
                if 'warehouse_name' in data:
                    updated_fields['name'] = data['warehouse_name']
                if 'warehouse_location' in data:
                    updated_fields['location'] = data['warehouse_location']

                # Update warehouse object
                Warehouse.objects.filter(pk=warehouse_id).update(**updated_fields)

                # Update products
                products_data = data.get('products', [])
                for product_data in products_data:
                    product_id = product_data.get('id')
                    if product_id:
                        Product.objects.filter(id=product_id).update(
                            name=product_data.get('name'),
                            weight=product_data.get('weight'),
                            amount=product_data.get('amount')
                        )
                    else:
                        # Create new product if product_id is not provided
                        Product.objects.create(
                            name=product_data.get('name'),
                            weight=product_data.get('weight'),
                            amount=product_data.get('amount'),
                            warehouse=warehouse
                        )

                # Update vehicles (similar logic as for products)
                vehicles_data = data.get('vehicles', [])
                for vehicle_data in vehicles_data:
                    vehicle_id = vehicle_data.get('id')
                    if vehicle_id:
                        Vehicle.objects.filter(id=vehicle_id).update(
                            name=vehicle_data.get('name'),
                            capacity=vehicle_data.get('capacity'),
                            fuel_amount=vehicle_data.get('fuel_amount')
                        )
                    else:
                        # Create new product if product_id is not provided
                        Vehicle.objects.create(
                            name=vehicle_data.get('name'),
                            capacity=vehicle_data.get('capacity'),
                            fuel_amount=vehicle_data.get('fuel_amount'),
                            warehouse=warehouse
                        )

                return JsonResponse({'success': True})
            else:
                pass

        except Warehouse.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Warehouse not found'}, status=404)
        except Exception as e:
            print(f"Error updating warehouse: {e}")
            return JsonResponse({'success': False, 'error': 'An error occurred'}, status=500)
    else:
        return JsonResponse({'success': False, 'error': 'Invalid request method'})

@csrf_exempt
def delete_product(request, product_id):
    if request.method == 'DELETE':
        product = get_object_or_404(Product, id=product_id)
        product.delete()
        return JsonResponse({'success': True})
    return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=400)

@csrf_exempt
def delete_vehicle(request, vehicle_id):
    if request.method == 'DELETE':
        vehicle = get_object_or_404(Vehicle, id=vehicle_id)
        vehicle.delete()
        return JsonResponse({'success': True})
    return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=400)

def create_warehouse(request):
  if request.method == 'POST':
    warehouse_name = request.POST.get('warehouse_name')
    warehouse_location = request.POST.get('warehouse_location')

    # Create a new warehouse object and save it to the database
    warehouse = Warehouse.objects.create(
        name=warehouse_name, location=warehouse_location, user=request.user
    )

    # Handle product form data
    product_names = request.POST.getlist('product_name')  # Get list of product names
    product_weights = [float(value) for value in request.POST.getlist('product_weight')]  # Convert to float
    product_amounts = [int(value) for value in request.POST.getlist('product_amount')]  # Convert to int

    # Create new product objects for each valid entry (using a loop)
    for i in range(len(product_names)):
      if product_names[i]:  # Check if product name is not empty
        Product.objects.create(
            name=product_names[i],
            weight=product_weights[i],
            amount=product_amounts[i],
            warehouse=warehouse,  # Link the product to the created warehouse
        )

    # Handle vehicle form data (similar logic as for products)
    vehicle_names = request.POST.getlist('vehicle_name')
    vehicle_capacities = [float(value) for value in request.POST.getlist('vehicle_capacity')]
    vehicle_fuel_amounts = [float(value) for value in request.POST.getlist('vehicle_fuel_amount')]

    for i in range(len(vehicle_names)):
      if vehicle_names[i]:  # Check if product name is not empty
        Vehicle.objects.create(
            name=vehicle_names[i],
            capacity=vehicle_capacities[i],
            fuel_amount=vehicle_fuel_amounts[i],
            warehouse=warehouse,  # Link the product to the created warehouse
        )
    
    # Redirect to a success URL after successful creation
    return redirect('main3')  # Redirect to page listing warehouses

  else:
    # Render the form template
    return render(request, 'main2.html')
  
# def create_products(request, warehouse_id):
#   if request.method == 'POST':

#     warehouse = Warehouse.objects.get(pk=warehouse_id)

#     # Handle product form data
#     product_names = request.POST.getlist('product_name')  # Get list of product names
#     product_weights = [float(value) for value in request.POST.getlist('product_weight')]  # Convert to float
#     product_amounts = [int(value) for value in request.POST.getlist('product_amount')]  # Convert to int

#     # Create new product objects for each valid entry (using a loop)
#     for i in range(len(product_names)):
#       if product_names[i]:  # Check if product name is not empty
#         Product.objects.create(
#             name=product_names[i],
#             weight=product_weights[i],
#             amount=product_amounts[i],
#             warehouse=warehouse,  # Link the product to the created warehouse
#         )
    
#     # Redirect to a success URL after successful creation
#     return redirect('main3')  # Redirect to page listing warehouses

#   else:
#     # Render the form template
#     return render(request, 'main2.html')

from django.http import JsonResponse
from .models import Warehouse, Order

def get_warehouse_details(request, warehouse_id):
    try:
        warehouse = Warehouse.objects.get(pk=warehouse_id)
        products = warehouse.product_set.all()
        vehicles = warehouse.vehicle_set.all()
        data = {
            'name': warehouse.name,
            'location': warehouse.location,
            'products': [{'id': product.id, 'name': product.name, 'weight': product.weight, 'amount': product.amount} for product in products],
            'vehicles': [{'id': vehicle.id, 'name': vehicle.name, 'capacity': vehicle.capacity, 'fuel_amount': vehicle.fuel_amount} for vehicle in vehicles]
        }
        return JsonResponse(data)
    except Warehouse.DoesNotExist:
        return JsonResponse({'error': 'Warehouse not found'}, status=404)
    
def create_order(request):
    if request.method == 'POST':
        order_name = request.POST.get('order_name')
        end_input = request.POST.get('end_input')
        start_input = request.POST.get('start_input')
        order_status = 0
        order_priority = request.POST.get('priority')
        warehouse_id = request.POST.get('warehouse_id')  # Get the posted warehouse ID

        # Create a new order object
        order = Order.objects.create(
            name=order_name,
            destination=end_input,
            starting_point=start_input,
            status=order_status,
            priority=order_priority,
            user=request.user,
        )

        # Save selected products (if any)
        selected_products = request.POST.getlist('options[]')  # Get selected product IDs
        amount_list = request.POST.getlist('amount[]')  # Get amounts for each product

        for product_id, amount in zip(selected_products, amount_list):
            product = Product.objects.get(pk=product_id)
            amount = int(amount)  # Ensure amount is an integer

            # Create Order_product object with product.name, product.weight, and amount
            Order_product.objects.create(
                order=order,
                warehouse=Warehouse.objects.get(pk=warehouse_id),
                name=product.name,  # Save product name explicitly
                weight=product.weight,  # Save product weight explicitly
                amount=amount,  # Save amount from the form
            )

        vehicle_name = request.POST.get('vehicle_name')  # Modify field names if needed
        vehicle_capacity = request.POST.get('vehicle_capacity')
        vehicle_fuel_amount = request.POST.get('vehicle_fuel_amount')

        # Create an Order_vehicle object
        Order_vehicle.objects.create(
            order=order,
            name=vehicle_name,
            capacity=vehicle_capacity,
            fuel_amount=vehicle_fuel_amount,
            warehouse=Warehouse.objects.get(pk=warehouse_id),
        )

        # Redirect to a success URL after successful creation
        return redirect('main2')  # Redirect to page listing orders (assuming typo)

    else:
        # Render the form template
        return render(request, 'main3.html')

from django.core import serializers
from django.http import JsonResponse

def get_order_details(request, order_id):
    try:
        order = Order.objects.get(pk=order_id)
        order_products = Order_product.objects.filter(order=order)
        order_vehicles = Order_vehicle.objects.filter(order=order)
        
        data = {
            'name': order.name,
            'destination': order.destination,
            'starting_point': order.starting_point,
            'priority': order.priority,
            'status': order.status,
            'order_products': list(order_products.values('name', 'weight', 'amount')),
            'order_vehicles': list(order_vehicles.values('name', 'capacity', 'fuel_amount'))
        }
        return JsonResponse(data)
    except Order.DoesNotExist:
        return JsonResponse({'error': 'Order not found'}, status=404)

from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Product, Warehouse  # Import models

from rest_framework import status

@api_view(['GET'])
def get_warehouse_by_product(request, product_id):
    product = get_object_or_404(Product, pk=product_id)

    # Assuming a foreign key from Warehouse to Product
    warehouse = product.warehouse  # Access the related warehouse object

    if warehouse:
        data = {
            'id': warehouse.id,
            'name': warehouse.name,
            'location': warehouse.location
        }
        return Response(data, status=status.HTTP_200_OK)
    else:
        return Response({'error': 'Warehouse not found'}, status=status.HTTP_404_NOT_FOUND)
    
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Vehicle
from .serializers import VehicleSerializer

@api_view(['GET'])
def get_vehicle_by_warehouse(request, warehouse_id):
  vehicles = Vehicle.objects.filter(warehouse_id=warehouse_id)
  if not vehicles.exists():
    return Response({"error": "No vehicles found for the given warehouse_id"}, status=404)
  serializer = VehicleSerializer(vehicles, many=True)  # Serialize all vehicles
  return Response(serializer.data)
    
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from .models import Order
 
def update_order_status(request, order_id):
    if request.method == 'PUT':
        try:
            status_data = json.loads(request.body)
            new_status = status_data.get('status')

            if new_status is not None:
                # Use filter() followed by update() to directly update the object in the database
                Order.objects.filter(pk=order_id).update(status=new_status)
                return JsonResponse({'message': 'Order status updated successfully!'})
            else:
                return JsonResponse({'error': 'Missing status data in request body'}, status=400)

        except Order.DoesNotExist:
            return JsonResponse({'error': 'Order not found'}, status=404)

        except Exception as e:
            print(f"An error occurred while updating order status: {e}")
            return JsonResponse({'error': 'An error occurred'}, status=500)

    else:
        return JsonResponse({'error': 'Method not allowed'}, status=405)

from django.shortcuts import get_object_or_404, redirect
from django.http import JsonResponse
from .models import Warehouse

def delete_warehouse(request, warehouse_id):
    if request.method == "DELETE":
        warehouse = get_object_or_404(Warehouse, id=warehouse_id)
        warehouse.delete()
        return JsonResponse({"success": True})
    else:
        return JsonResponse({"error": "Invalid request method"}, status=400)
    
def delete_order(request, order_id):
    if request.method == "DELETE":
        order = get_object_or_404(Order, id=order_id)
        order.delete()
        return JsonResponse({"success": True})
    else:
        return JsonResponse({"error": "Invalid request method"}, status=400)