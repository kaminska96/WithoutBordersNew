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
    return render(request, 'registrationapp/main3.html')

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

from django.shortcuts import render, redirect
from .models import Warehouse

def create_warehouse(request):
    if request.method == 'POST':
        warehouse_name = request.POST.get('warehouse_name')
        warehouse_location = request.POST.get('warehouse_location')

        # Create a new warehouse object and save it to the database
        warehouse = Warehouse.objects.create(
            name=warehouse_name, location=warehouse_location, user=request.user
        )

        # Handle product form data (assuming it's also included in the POST request)
        product_name = request.POST.get('product_name')  # Get a list of product names
        product_weight = request.POST.get('product_weight')  # Get a list of product weights (decimal)
        product_amount = request.POST.get('product_amount')  # Get a list of product amounts (integers)


        # Create a new product object for each valid entry
        Product.objects.create(
            name=product_name,
            weight=product_weight,
            amount=product_amount,
            warehouse=warehouse,  # Link the product to the created warehouse
        )

        # Handle vehicle form data (similar logic as for products)
        vehicle_name = request.POST.get('vehicle_name')
        vehicle_capacity = request.POST.get('vehicle_capacity')
        vehicle_fuel_amount = request.POST.get('vehicle_fuel_amount')

        # Create a new vehicle object for each valid entry
        Vehicle.objects.create(
            name=vehicle_name,
            capacity=vehicle_capacity,
            fuel_amount=vehicle_fuel_amount,
            warehouse=warehouse,  # Link the vehicle to the created warehouse
        )

        # Redirect to a success URL after successful creation
        return redirect('main3')  # Redirect to page listing warehouses

    else:
        # Render the form template
        return render(request, 'main2.html')
