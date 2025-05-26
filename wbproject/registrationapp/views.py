from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from django.contrib import messages, auth
from django.http import JsonResponse
from .serializers import VehicleSerializer
from .models import Order, Order_product, Order_vehicle, Product, Vehicle, Warehouse, Order_destinations, Order_warehouses
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

import logging
logger = logging.getLogger(__name__)

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


# def order_detail_api(request, order_id):
#     try:
#         order = Order.objects.get(pk=order_id)
#         order_products = Order_product.objects.filter(order=order)
#         order_vehicles = Order_vehicle.objects.filter(order=order)
        
#         data = {
#             'name': order.name,
#             'destination': order.destination,
#             'starting_point': order.starting_point,
#             'priority': order.priority,
#             'status': order.status,
#             'order_products': list(order_products.values('id', 'name', 'weight', 'amount')),
#             'order_vehicles': list(order_vehicles.values('id', 'name', 'capacity', 'fuel_amount'))
#         }
#         return JsonResponse(data)
#     except Order.DoesNotExist:
#         return JsonResponse({'error': 'Order not found'}, status=404)
    


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
    orders = Order.objects.filter(user=request.user, status=0)\
           .prefetch_related('order_warehouses', 'order_destinations')\
           .order_by('priority')
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
        #
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
                            fuel_amount=vehicle_data.get('fuel_amount'),
                            fuel_type=vehicle_data.get('fuel_type')
                        )
                    else:

                        Vehicle.objects.create(
                            name=vehicle_data.get('name'),
                            capacity=vehicle_data.get('capacity'),
                            fuel_amount=vehicle_data.get('fuel_amount'),
                            fuel_type=vehicle_data.get('fuel_type'),
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
    vehicle_fuel_types = request.POST.getlist('vehicle_fuel_type')

    for i in range(len(vehicle_names)):
      if vehicle_names[i]: 
        Vehicle.objects.create(
            name=vehicle_names[i],
            capacity=vehicle_capacities[i],
            fuel_amount=vehicle_fuel_amounts[i],
            fuel_type=vehicle_fuel_types[i] if i < len(vehicle_fuel_types) else 'Бензин А-95',
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
            'vehicles': [{'id': vehicle.id, 'name': vehicle.name, 'capacity': vehicle.capacity, 'fuel_amount': vehicle.fuel_amount, 'fuel_type': vehicle.fuel_type} for vehicle in vehicles]
        }
        return JsonResponse(data)
    except Warehouse.DoesNotExist:
        return JsonResponse({'error': 'Warehouse not found'}, status=404)
    

def create_order(request):
    if request.method == 'POST':
        print(request.POST)
        try:
            # 1. Create the main Order
            order = Order.objects.create(
                name=request.POST.get('order_name'),
                priority=int(request.POST.get('priority', 1)),
                planned_date=request.POST.get('planned_date'),
                estimated_end=request.POST.get('estimated_date'),
                user=request.user,
                status=0  # Pending
            )
            
            # 2. Save Order destinations
            destinations = request.POST.getlist('end_input[]')
            for dest in destinations:
                if dest.strip():  # Only save non-empty destinations
                    Order_destinations.objects.create(
                        destination=dest,
                        order=order
                    )
            
            # 3. Save Order warehouses
            warehouse_ids = request.POST.get('warehouse_id', '').split(',')
            for warehouse_id in warehouse_ids:
                if warehouse_id.strip():  # Only process valid IDs
                    try:
                        warehouse = Warehouse.objects.get(id=warehouse_id)
                        Order_warehouses.objects.create(
                            warehouse_location=warehouse.location,
                            warehouse=warehouse,
                            order=order
                        )
                    except Warehouse.DoesNotExist:
                        pass  # Skip invalid warehouse IDs
            
            # 4. Save Order vehicles
            vehicle_names = request.POST.get('vehicle_name', '').split(',')
            vehicle_capacities = request.POST.get('vehicle_capacity', '').split(',')
            vehicle_fuel_amounts = request.POST.get('vehicle_fuel_amount', '').split(',')
            vehicle_fuel_types = request.POST.get('vehicle_fuel_type', '').split(',')
            
            for i in range(len(vehicle_names)):
                if i < len(vehicle_capacities) and i < len(vehicle_fuel_amounts):
                    # Default to first warehouse if multiple exist
                    warehouse = Warehouse.objects.filter(id__in=warehouse_ids).first()
                    
                    Order_vehicle.objects.create(
                        name=vehicle_names[i],
                        capacity=float(vehicle_capacities[i]),
                        fuel_amount=float(vehicle_fuel_amounts[i]),
                        fuel_type=vehicle_fuel_types[i],
                        warehouse=warehouse,
                        order=order
                    )
            
            # 5. Fixed: Save Order products
            # Get all destination indices that have products
            product_fields = [k for k in request.POST if k.startswith('options[')]
            dest_indices = list({k.split('[')[1].split(']')[0] for k in product_fields})
            for dest_index in dest_indices:
                # Get products and amounts for this destination
                product_ids = request.POST.getlist(f'options[{dest_index}][]')
                amounts = request.POST.getlist(f'amount[{dest_index}][]')
                # зберігаємо усі створені Order_destinations у список, щоб не шукати двічі
                dest_qs = list(Order_destinations.objects.filter(order=order).order_by('id'))
                dest_obj = dest_qs[int(dest_index) - 1]   # ← мінус один
                
                # Create order products
                for product_id, amount in zip(product_ids, amounts):
                    
                    product = Product.objects.get(id=product_id)
                    # Варіант А — звичайний print (додайте flush=True, щоб не було буферизації)
                    print('PRODUCT:', product.id, product.name, product.weight, product.warehouse, flush=True)
                    print('Amount:', amount, flush=True)
                    print('dest_obj:', dest_obj.id, dest_obj.destination, dest_obj.order, flush=True)
                    # print('DEST:', dest_obj, flush=True)

                    # Варіант Б — logging (бажано у продакшені)
                    logger.debug('Amount %s ', amount)
                    # logger.debug('DEST %s ', dest_obj)
                    Order_product.objects.create(
                        name=product.name,
                        weight=product.weight,
                        amount=int(amount),
                        warehouse=product.warehouse,
                        order_destinations=dest_obj
                    )

            logger.debug('POST data: %s', request.POST)
            return redirect('planned_orders')

        except Exception as e:
            messages.error(request, f'Помилка: {str(e)}')
            return redirect('creating_order')
    
    # GET request - show form
    return render(request, 'registrationapp/creating_order.html')


def get_order_details(request, order_id):
    try:
        order = Order.objects.get(pk=order_id)
        
        # Get all destinations for this order
        destinations = Order_destinations.objects.filter(order=order)
        destination_data = []

        for dest in destinations:
            # Get products for this specific destination
            dest_products = Order_product.objects.filter(order_destinations=dest)
            
            products_list = [{
                'id': op.id,
                'name': op.name,
                'weight': op.weight,
                'amount': op.amount,
                'warehouse': op.warehouse.name if op.warehouse else 'Unknown Warehouse'
            } for op in dest_products]
            
            destination_data.append({
                'id': dest.id,
                'destination': dest.destination,
                'products': products_list
            })
        
        # Get all warehouses for this order
        warehouses = Order_warehouses.objects.filter(order=order)
        warehouse_list = [{
            'id': wh.warehouse.id if wh.warehouse else None,
            'name': wh.warehouse.name if wh.warehouse else wh.warehouse_location,
            'location': wh.warehouse_location
        } for wh in warehouses]
        
        # Get starting point (first warehouse location)
        starting_point = warehouse_list[0]['location'] if warehouse_list else ''
        
        
        # Get all vehicles for this order
        order_vehicles = Order_vehicle.objects.filter(order=order)
        vehicles_list = [{
            'id': ov.id,
            'name': ov.name,
            'capacity': ov.capacity,
            'fuel_amount': ov.fuel_amount,
            'fuel_type': ov.fuel_type,
            'warehouse': ov.warehouse.name if ov.warehouse else 'Unknown Warehouse'
        } for ov in order_vehicles]
        
        data = {
            'id': order.id,
            'name': order.name,
            'priority': order.priority,
            'status': order.status,
            'planned_date': order.planned_date.strftime('%Y-%m-%d') if order.planned_date else None,
            'estimated_end': order.estimated_end.strftime('%Y-%m-%d') if order.estimated_end else None,
            'destinations': destination_data,  # Now includes nested products
            'warehouses': warehouse_list,
            'starting_point': starting_point,
            'vehicles': vehicles_list
        }
        
        return JsonResponse(data)
    
    except Order.DoesNotExist:
        return JsonResponse({'error': 'Order not found'}, status=404)
    except Exception as e:
        # Log the full error for debugging
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': str(e), 'traceback': traceback.format_exc()}, status=500)
    

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
        # orders = Order.objects.filter(Q(name__icontains=query) | Q(destination__icontains=query)| Q(starting_point__icontains=query), user=user)
        orders = Order.objects.filter(Q(name__icontains=query), user=user)
        order_data = [{'id': order.id, 
                       'name': order.name, 
                    #    'destination': order.destination,
                    #    'starting_point': order.starting_point,
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


from bs4 import BeautifulSoup
from datetime import datetime

def scrape_minfin_fuel_prices():
    """
    Scrapes current fuel prices from Minfin website
    Returns a dictionary with fuel types and their prices in UAH
    """
    url = "https://index.minfin.com.ua/ua/markets/fuel/"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    try:
        # Send request and parse HTML
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find the fuel prices table
        table = soup.find('table', {'class': 'line'})
        if not table:
            raise ValueError("Fuel prices table not found")
        
        # Extract prices from table rows
        prices = {}
        for row in table.find_all('tr')[1:]:  # Skip header row
            cols = row.find_all('td')
            if len(cols) >= 3:
                fuel_type = cols[0].get_text(strip=True)
                price_text = cols[2].get_text(strip=True)
                
                # Clean the fuel type name
                fuel_type = fuel_type.replace('Бензин', '').replace('преміум', '').strip()
                fuel_type = fuel_type.replace('А-', 'A-').strip()  # Standardize naming
                
                # Extract price (it's inside a <big> tag in the HTML)
                price = price_text.replace(',', '.').replace('грн', '').strip()
                
                # Only add if we have a valid price
                if price.replace('.', '').isdigit():
                    prices[fuel_type] = float(price)
        
        # Get last update time
        update_time = soup.find('div', {'class': 'idx-updatetime'})
        if update_time:
            update_text = update_time.get_text(strip=True)
            # Extract datetime part
            update_datetime = update_text.split(':')[-1].strip()
        
        return {
            'prices': prices,
            'last_updated': update_datetime if update_time else None,
            'source': url,
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        print(f"Scraping failed: {str(e)}")
        return None

def get_fuel_prices(request):
    try:
        fuel_data = scrape_minfin_fuel_prices()
        if fuel_data:
            return JsonResponse(fuel_data)
        else:
            # Return fallback data if scraping fails
            return JsonResponse({
                'prices': {
                    'A-95 преміум': 58.70,
                    'A-95': 54.47,
                    'A-92': 51.95,
                    'Дизельне паливо': 52.61,
                    'Газ автомобільний': 34.90
                },
                'last_updated': '23.05.2025 13:18',
                'source': 'https://index.minfin.com.ua/ua/markets/fuel/',
                'timestamp': datetime.now().isoformat(),
                'note': 'Using fallback data as scraping failed'
            })
    except Exception as e:
        return JsonResponse({
            'error': str(e),
            'status': 'Scraping failed'
        }, status=500)