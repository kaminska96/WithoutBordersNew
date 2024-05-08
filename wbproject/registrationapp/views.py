from django.shortcuts import render
from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from django.contrib import messages, auth
# from withoutborders.models import Profile
from django.contrib import auth
from django.http import JsonResponse
from .models import Product, Vehicle, Warehouse
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
    return render(request, 'registrationapp/main.html')

def main2(request):
    if not request.user.is_authenticated:
        return redirect('login')
    return render(request, 'registrationapp/main2.html')

def main3(request): 
    if not request.user.is_authenticated:
        return redirect('login')
    warehouses = Warehouse.objects.all()  # Fetch all warehouses
    context = {'warehouses': warehouses}
    return render(request, 'registrationapp/main3.html', context)

@csrf_exempt
def updateWarehouse(request, warehouse_id):
    if request.method == 'POST':
        try:
            warehouse = Warehouse.objects.get(id=warehouse_id)
        except Warehouse.DoesNotExist:
            return JsonResponse({'error': 'Warehouse not found'}, status=404)

        data = json.loads(request.body.decode('utf-8'))
        name = data.get('name')
        location = data.get('location')

        warehouse.name = name
        warehouse.location = location
        warehouse.save()

        return JsonResponse({'message': 'Warehouse updated successfully'}, status=200)

    return JsonResponse({'error': 'Invalid request method'}, status=400)

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

from django.http import JsonResponse
from django.shortcuts import get_object_or_404

from .models import Warehouse  # Replace with your warehouse model

def warehouse_details(request, warehouse_id):
  """
  Fetches and returns details of a specific warehouse identified by warehouse_id.
  """
  warehouse = get_object_or_404(Warehouse, pk=warehouse_id)
  serialized_data = {
      'name': warehouse.name,
      'location': warehouse.location,
      'products': [
          {
              'name': product.name,
              'weight': product.weight,
              'amount': product.amount,
          }
          for product in warehouse.products.all()
      ],
      'vehicles': [
          {
              'name': vehicle.name,
              'capacity': vehicle.capacity,
              'fuel_amount': vehicle.fuel_amount,
          }
          for vehicle in warehouse.vehicles.all()
      ],
  }
  return JsonResponse(serialized_data)
