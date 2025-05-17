from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from django.contrib import messages, auth
from django.http import JsonResponse
from .serializers import VehicleSerializer
from .models import Order, Order_product, Order_vehicle, Product, Vehicle, Warehouse
from django.views.decorators.csrf import csrf_exempt
import json
from django.views import View
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Q
from datetime import datetime, timedelta
from django.utils import timezone
from datetime import date, timedelta
from calendar import monthrange

def calendar(request):
    if not request.user.is_authenticated:
        return redirect('login')

    now = timezone.now()
    year = request.GET.get('year', now.year)
    month = request.GET.get('month', now.month)

    try:
        year = int(year)
        month = int(month)
        current_date = date(year, month, 1)
    except (ValueError, TypeError):
        current_date = now.date()
        year = current_date.year
        month = current_date.month

    # Get first and last day of month
    _, last_day = monthrange(year, month)
    first_day = date(year, month, 1)
    last_day = date(year, month, last_day)

    # Get orders for the month
    orders = Order.objects.filter(
        planned_date__date__range=[first_day, last_day],
        user=request.user
    ).order_by('planned_date')

    # Create calendar structure organized by weeks
    calendar_weeks = []
    current_week = []
    
    # Add days from previous month
    first_weekday = first_day.weekday()
    prev_month_last_day = first_day - timedelta(days=1)
    for i in range(first_weekday):
        day = prev_month_last_day.day - (first_weekday - i - 1)
        current_week.append({
            'day': day,
            'in_month': False,
            'is_today': False,
            'orders': []
        })

    # Add days from current month
    today = now.date()
    for day in range(1, last_day.day + 1):
        current_day = date(year, month, day)
        day_orders = [o for o in orders if o.planned_date.date() == current_day]
        current_week.append({
            'day': day,
            'in_month': True,
            'is_today': current_day == today,
            'orders': day_orders
        })
        
        # Start new week on Sunday
        if len(current_week) == 7:
            calendar_weeks.append(current_week)
            current_week = []

    # Add days from next month
    last_weekday = last_day.weekday()
    next_month_days = 6 - last_weekday
    for day in range(1, next_month_days + 1):
        current_week.append({
            'day': day,
            'in_month': False,
            'is_today': False,
            'orders': []
        })
    
    # Add the last week if not empty
    if current_week:
        # Fill remaining days if needed
        while len(current_week) < 7:
            current_week.append({
                'day': '',
                'in_month': False,
                'is_today': False,
                'orders': []
            })
        calendar_weeks.append(current_week)

    context = {
        'current_year': year,
        'current_month': month,
        'month_name': get_month_name(month),
        'prev_month': get_previous_month(year, month),
        'next_month': get_next_month(year, month),
        'calendar_weeks': calendar_weeks,
    }

    return render(request, 'registrationapp/calendar.html', context)

def get_month_name(month):
    """Returns the Ukrainian month name for the given month number"""
    months = {
        1: 'Січень',
        2: 'Лютий',
        3: 'Березень',
        4: 'Квітень',
        5: 'Травень',
        6: 'Червень',
        7: 'Липень',
        8: 'Серпень',
        9: 'Вересень',
        10: 'Жовтень',
        11: 'Листопад',
        12: 'Грудень'
    }
    return months.get(month, '')

def get_previous_month(year, month):
    """Returns the previous month and year"""
    if month == 1:
        return (year - 1, 12)
    else:
        return (year, month - 1)

def get_next_month(year, month):
    """Returns the next month and year"""
    if month == 12:
        return (year + 1, 1)
    else:
        return (year, month + 1)


def order_detail_api(request, order_id):
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
            'order_products': list(order_products.values('id', 'name', 'weight', 'amount')),
            'order_vehicles': list(order_vehicles.values('id', 'name', 'capacity', 'fuel_amount'))
        }
        return JsonResponse(data)
    except Order.DoesNotExist:
        return JsonResponse({'error': 'Order not found'}, status=404)
    


class Index(View):
    def get(self, request):
        return render(request, 'registrationapp/withoutborders.html')


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
                messages.info(request, 'Цей email вже використовується!')
                return redirect('signup')
            elif User.objects.filter(username=username).exists():
                messages.info(request, 'Це ім’я користувача вже зайнято!')
                return redirect('signup')
            else:
                user = User.objects.create_user(first_name=first_name, last_name=last_name, username=username, email=email, password=password)
                user.save()

                user_model = User.objects.get(username=username)

                return redirect('login')
        else:
            messages.info(request, 'Паролі не співпадають!')
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
            return redirect('planned_orders')
        else:
            messages.info(request, 'Неправильні дані')
            return redirect('login')
    else:
        return render(request, 'registrationapp/login.html')
    

def planned_orders(request):
    if not request.user.is_authenticated:
        return redirect('login')
    orders = Order.objects.filter(user=request.user) 
    context = {'orders': orders}
    return render(request, 'registrationapp/planned_orders.html', context)


def orders_on_the_way(request):
    if not request.user.is_authenticated:
        return redirect('login')
    orders = Order.objects.filter(user=request.user) 
    context = {'orders': orders}
    return render(request, 'registrationapp/orders_on_the_way.html', context)


def completed_orders(request):
    if not request.user.is_authenticated:
        return redirect('login')
    orders = Order.objects.filter(user=request.user) 
    context = {'orders': orders}
    return render(request, 'registrationapp/completed_orders.html', context)


def creating_order(request):
    if not request.user.is_authenticated:
        return redirect('login')

    warehouses = Warehouse.objects.filter(user=request.user)

    if not warehouses.exists():
        products = []
    else:
        
        product_ids = [list(warehouse.product_set.all().values_list('id', flat=True)) for warehouse in warehouses]

        product_ids = sum(product_ids, [])

        products = Product.objects.filter(id__in=product_ids).distinct()

    context = {'products': products}
    return render(request, 'registrationapp/creating_order.html', context)


def warehouses(request): 
    if not request.user.is_authenticated:
        return redirect('login')
    warehouses = Warehouse.objects.filter(user=request.user)
    context = {'warehouses': warehouses}
    return render(request, 'registrationapp/warehouses.html', context)


def update_warehouse(request, warehouse_id):
    if request.method == 'PUT': 
        try:
            warehouse = Warehouse.objects.get(id=warehouse_id)
            if request.content_type == 'application/json':
                data = json.loads(request.body)
                updated_fields = {}
                if 'warehouse_name' in data:
                    updated_fields['name'] = data['warehouse_name']
                if 'warehouse_location' in data:
                    updated_fields['location'] = data['warehouse_location']

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

                # Update vehicles
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

    warehouse = Warehouse.objects.create(
        name=warehouse_name, location=warehouse_location, user=request.user
    )

    product_names = request.POST.getlist('product_name')
    product_weights = [float(value) for value in request.POST.getlist('product_weight')] 
    product_amounts = [int(value) for value in request.POST.getlist('product_amount')]

    for i in range(len(product_names)):
      if product_names[i]: 
        Product.objects.create(
            name=product_names[i],
            weight=product_weights[i],
            amount=product_amounts[i],
            warehouse=warehouse,
        )

    vehicle_names = request.POST.getlist('vehicle_name')
    vehicle_capacities = [float(value) for value in request.POST.getlist('vehicle_capacity')]
    vehicle_fuel_amounts = [float(value) for value in request.POST.getlist('vehicle_fuel_amount')]

    for i in range(len(vehicle_names)):
      if vehicle_names[i]: 
        Vehicle.objects.create(
            name=vehicle_names[i],
            capacity=vehicle_capacities[i],
            fuel_amount=vehicle_fuel_amounts[i],
            warehouse=warehouse,
        )
    
    return redirect('warehouses') 

  else:
    # Render the form template
    return render(request, 'creating_order.html')


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
        estimated_date = request.POST.get('estimated_date')
        planned_date = request.POST.get('planned_date')
        order_priority = request.POST.get('priority')
        warehouse_id = request.POST.get('warehouse_id')

        # Create a new order object
        order = Order.objects.create(
            name=order_name,
            destination=end_input,
            starting_point=start_input,
            status=order_status,
            priority=order_priority,
            user=request.user,
            estimated_end=estimated_date,
            planned_date=planned_date,
        )

        selected_products = request.POST.getlist('options[]')
        amount_list = request.POST.getlist('amount[]')

        for product_id, amount in zip(selected_products, amount_list):
            product = Product.objects.get(pk=product_id)
            amount = int(amount) 

            Order_product.objects.create(
                order=order,
                warehouse=Warehouse.objects.get(pk=warehouse_id),
                name=product.name,  
                weight=product.weight, 
                amount=amount, 
            )

        vehicle_name = request.POST.get('vehicle_name') 
        vehicle_capacity = request.POST.get('vehicle_capacity')
        vehicle_fuel_amount = request.POST.get('vehicle_fuel_amount')

        Order_vehicle.objects.create(
            order=order,
            name=vehicle_name,
            capacity=vehicle_capacity,
            fuel_amount=vehicle_fuel_amount,
            warehouse=Warehouse.objects.get(pk=warehouse_id),
        )

        return redirect('creating_order') 

    else:
        return render(request, 'warehouses.html')


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
            'order_products': list(order_products.values('id', 'name', 'weight', 'amount')),
            'order_vehicles': list(order_vehicles.values('id', 'name', 'capacity', 'fuel_amount'))
        }
        return JsonResponse(data)
    except Order.DoesNotExist:
        return JsonResponse({'error': 'Order not found'}, status=404)
    

@api_view(['GET'])
def get_warehouse_by_product(request, product_id):
    product = get_object_or_404(Product, pk=product_id)

    warehouse = product.warehouse 

    if warehouse:
        data = {
            'id': warehouse.id,
            'name': warehouse.name,
            'location': warehouse.location
        }
        return Response(data, status=status.HTTP_200_OK)
    else:
        return Response({'error': 'Warehouse not found'}, status=status.HTTP_404_NOT_FOUND)
    

@api_view(['GET'])
def get_vehicle_by_warehouse(request, warehouse_id):
  vehicles = Vehicle.objects.filter(warehouse_id=warehouse_id)
  if not vehicles.exists():
    return Response({"error": "No vehicles found for the given warehouse_id"}, status=404)
  serializer = VehicleSerializer(vehicles, many=True)
  return Response(serializer.data)
 

def update_order_status(request, order_id):
    if request.method == 'PUT':
        try:
            status_data = json.loads(request.body)
            new_status = status_data.get('status')

            if new_status is not None:
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
    
def search_orders(request):
    query = request.GET.get('query', '')
    user = request.user

    if query:
        orders = Order.objects.filter(Q(name__icontains=query) | Q(destination__icontains=query)| Q(starting_point__icontains=query), user=user)
        order_data = [{'id': order.id, 
                       'name': order.name, 
                       'destination': order.destination,
                       'starting_point': order.starting_point,
                       'priority': order.priority,
                       'status': order.status,} for order in orders]
        return JsonResponse({'orders': order_data})
    else:
        return JsonResponse({'orders': []})
    
import csv
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import pandas as pd

@require_POST
@csrf_exempt
def import_warehouse_goods(request):
    if not request.FILES.get('file'):
        return JsonResponse({'success': False, 'error': 'No file provided'})
    
    warehouse_id = request.POST.get('warehouse_id')
    file_type = request.POST.get('file_type', 'csv')
    has_headers = request.POST.get('has_headers', 'false') == 'true'
    
    try:
        warehouse = Warehouse.objects.get(id=warehouse_id)
    except Warehouse.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Warehouse not found'})
    
    try:
        if file_type == 'csv':
            # Process CSV file
            file = request.FILES['file']
            decoded_file = file.read().decode('utf-8').splitlines()
            reader = csv.reader(decoded_file)
            
            if has_headers:
                next(reader)  # Skip header row
                
            imported_count = 0
            for row in reader:
                if len(row) >= 3:
                    Product.objects.create(
                        warehouse=warehouse,
                        name=row[0].strip(),
                        weight=float(row[1].strip()),
                        amount=int(row[2].strip())
                    )
                    imported_count += 1
                    
        else:
            # Process Excel file
            file = request.FILES['file']
            df = pd.read_excel(file, header=0 if has_headers else None)
            
            imported_count = 0
            for _, row in df.iterrows():
                Product.objects.create(
                    warehouse=warehouse,
                    name=str(row[0]).strip(),
                    weight=float(row[1]),
                    amount=int(row[2])
                )
                imported_count += 1
                
        return JsonResponse({'success': True, 'imported_count': imported_count})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


