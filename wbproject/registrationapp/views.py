from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from django.contrib import messages, auth
from django.http import JsonResponse
from .serializers import VehicleSerializer
from .models import Order, Order_product, Order_vehicle, Product, Vehicle, Warehouse, Order_destinations, Order_warehouses, Driver, Order_driver
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
from django.core.mail import send_mail
from django.http import HttpResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required

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

    _, last_day = monthrange(year, month)
    first_day = date(year, month, 1)
    last_day = date(year, month, last_day)

    orders = Order.objects.filter(
        planned_date__date__range=[first_day, last_day],
        user=request.user
    ).order_by('planned_date')

    calendar_weeks = []
    current_week = []
    
    first_weekday = first_day.weekday()
    if first_weekday != 0:
        prev_month_last_day = first_day - timedelta(days=1)
        for i in range(first_weekday):
            day = prev_month_last_day.day - (first_weekday - i - 1)
            current_week.append({
                'day': day,
                'in_month': False,
                'is_today': False,
                'orders': []
            })

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
        
        if len(current_week) == 7:
            calendar_weeks.append(current_week)
            current_week = []

    last_weekday = last_day.weekday() 
    if last_weekday != 6:
        next_month_days = 6 - last_weekday
        for day in range(1, next_month_days + 1):
            current_week.append({
                'day': day,
                'in_month': False,
                'is_today': False,
                'orders': []
            })
    if current_week:
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

                auth.login(request, user)
                return redirect('planned_orders')
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
                        Product.objects.create(
                            name=product_data.get('name'),
                            weight=product_data.get('weight'),
                            amount=product_data.get('amount'),
                            warehouse=warehouse
                        )

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
            order = Order.objects.create(
                name=request.POST.get('order_name'),
                priority=int(request.POST.get('priority', 1)),
                planned_date=request.POST.get('planned_date'),
                estimated_end=request.POST.get('estimated_date'),
                user=request.user,
                status=0 
            )
            
            destinations = request.POST.getlist('end_input[]')
            for dest in destinations:
                if dest.strip():  
                    Order_destinations.objects.create(
                        destination=dest,
                        order=order
                    )
            
            warehouse_ids = request.POST.get('warehouse_id', '').split(',')
            for warehouse_id in warehouse_ids:
                if warehouse_id.strip(): 
                    try:
                        warehouse = Warehouse.objects.get(id=warehouse_id)
                        Order_warehouses.objects.create(
                            warehouse_location=warehouse.location,
                            warehouse=warehouse,
                            order=order
                        )
                    except Warehouse.DoesNotExist:
                        pass  
            
            vehicle_names = request.POST.get('vehicle_name', '').split(',')
            vehicle_capacities = request.POST.get('vehicle_capacity', '').split(',')
            vehicle_fuel_amounts = request.POST.get('vehicle_fuel_amount', '').split(',')
            vehicle_fuel_types = request.POST.get('vehicle_fuel_type', '').split(',')
            
            driver_ids = request.POST.get('vehicle_driver', '').split(',')
            
            for i in range(len(vehicle_names)):
                if (i < len(vehicle_capacities) and 
                    i < len(vehicle_fuel_amounts) and 
                    i < len(vehicle_fuel_types)):
                    
                    warehouse = Warehouse.objects.filter(id__in=warehouse_ids).first()
                    
                    vehicle = Order_vehicle.objects.create(
                        name=vehicle_names[i],
                        capacity=float(vehicle_capacities[i]),
                        fuel_amount=float(vehicle_fuel_amounts[i]),
                        fuel_type=vehicle_fuel_types[i],
                        warehouse=warehouse,
                        order=order
                    )
                    
                    if i < len(driver_ids) and driver_ids[i]:
                        try:
                            driver = Driver.objects.get(id=driver_ids[i])
                            print(f"Assigning driver ID: {driver.id}")
                            print(f"Name: {driver.name}")
                            print(f"Surname: {driver.surname}")
                            print(f"Phone: {driver.phone}")
                            print(f"Email: {driver.email}")
                            Order_driver.objects.create(
                                name=driver.name,
                                surname=driver.surname,
                                phone=driver.phone,
                                email=driver.email,
                                order_vehicle=vehicle
                            )
                        except Driver.DoesNotExist:
                            messages.warning(request, f"Водій не знайдений для {vehicle.name}")
            
            product_fields = [k for k in request.POST if k.startswith('options[')]
            dest_indices = list({k.split('[')[1].split(']')[0] for k in product_fields})
            
            destinations = list(Order_destinations.objects.filter(order=order).order_by('id'))
            
            for dest_index in dest_indices:
                product_ids = request.POST.getlist(f'options[{dest_index}][]')
                amounts = request.POST.getlist(f'amount[{dest_index}][]')
                
                try:
                    dest_obj = destinations[int(dest_index) - 1]
                except IndexError:
                    continue  
                
                for product_id, amount in zip(product_ids, amounts):
                    try:
                        amount_int = int(amount)
                        product = Product.objects.get(id=product_id)

                        if product.amount < amount_int:
                            raise ValueError(f"Недостатньо {product.name}. Доступно: {product.amount}, Просили: {amount_int}")
                        
                        Order_product.objects.create(
                            name=product.name,
                            weight=product.weight,
                            amount=amount_int,
                            warehouse=product.warehouse,
                            order_destinations=dest_obj
                        )

                        product.amount -= amount_int
                        product.save()
                    except (ValueError, Product.DoesNotExist) as e:
                        print(f"Error processing product: {e}")
                        continue

            return redirect('planned_orders')

        except Exception as e:
            print(f"Error creating order: {e}") 
            messages.error(request, f'Помилка: {str(e)}')
            return redirect('creating_order')
    
    return render(request, 'registrationapp/creating_order.html')


def get_order_details(request, order_id):
    try:
        order = Order.objects.get(pk=order_id)
        
        destinations = Order_destinations.objects.filter(order=order)
        destination_data = []

        for dest in destinations:
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
        
        warehouses = Order_warehouses.objects.filter(order=order)
        warehouse_list = [{
            'id': wh.warehouse.id if wh.warehouse else None,
            'name': wh.warehouse.name if wh.warehouse else wh.warehouse_location,
            'location': wh.warehouse_location
        } for wh in warehouses]
        
        starting_point = warehouse_list[0]['location'] if warehouse_list else ''
        
        order_vehicles = Order_vehicle.objects.filter(order=order)
        vehicles_list = []
        
        for ov in order_vehicles:
            driver_info = None
            try:
                driver = Order_driver.objects.get(order_vehicle=ov)
                driver_info = {
                    'id': driver.id,
                    'name': driver.name,
                    'surname': driver.surname,
                    'phone': driver.phone,
                    'email': driver.email
                }
            except Order_driver.DoesNotExist:
                pass
            
            vehicles_list.append({
                'id': ov.id,
                'name': ov.name,
                'capacity': ov.capacity,
                'fuel_amount': ov.fuel_amount,
                'fuel_type': ov.fuel_type,
                'warehouse': ov.warehouse.name if ov.warehouse else 'Unknown Warehouse',
                'driver': driver_info 
            })
        
        data = {
            'id': order.id,
            'name': order.name,
            'priority': order.priority,
            'status': order.status,
            'planned_date': order.planned_date.isoformat() if order.planned_date else None,
            'estimated_end': order.estimated_end.isoformat() if order.estimated_end else None,
            'destinations': destination_data,
            'warehouses': warehouse_list,
            'starting_point': starting_point,
            'vehicles': vehicles_list  
        }
        
        return JsonResponse(data)
    
    except Order.DoesNotExist:
        return JsonResponse({'error': 'Order not found'}, status=404)
    except Exception as e:
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
        try:
            order = get_object_or_404(Order, id=order_id)
            
            if order.status in [0, 1]:
                order_products = Order_product.objects.filter(
                    order_destinations__order=order
                ).select_related('warehouse')
                
                for order_product in order_products:
                    try:
                        product = order_product.warehouse.product_set.filter(
                            name=order_product.name,
                            weight=order_product.weight
                        ).first()
                        
                        if product:
                            product.amount += order_product.amount
                            product.save()
                    except Exception as e:
                        print(f"Error restoring product {order_product.id}: {str(e)}")
                        continue
            
            order.delete()
            
            return JsonResponse({"success": True})
        
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    
    else:
        return JsonResponse({"error": "Invalid request method"}, status=400)
    
def search_orders(request):
    query = request.GET.get('query', '')
    user = request.user

    if query:
        orders = Order.objects.filter(
            Q(name__icontains=query) |
            Q(order_destinations__destination__icontains=query) |
            Q(order_warehouses__warehouse_location__icontains=query),
            user=user
        ).distinct()

        order_data = []
        for order in orders:
            first_warehouse = order.order_warehouses.first()
            starting_point = first_warehouse.warehouse_location if first_warehouse else '—'

            last_destination = order.order_destinations.last()
            destination = last_destination.destination if last_destination else '—'

            order_data.append({
                'id': order.id,
                'name': order.name,
                'starting_point': starting_point,
                'destination': destination,
                'priority': order.priority,
                'status': order.status,
            })

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
            file = request.FILES['file']
            decoded_file = file.read().decode('utf-8').splitlines()
            reader = csv.reader(decoded_file)
            
            if has_headers:
                next(reader) 
                
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
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        table = soup.find('table', {'class': 'line'})
        if not table:
            raise ValueError("Fuel prices table not found")
        
        prices = {}
        for row in table.find_all('tr')[1:]: 
            cols = row.find_all('td')
            if len(cols) >= 3:
                fuel_type = cols[0].get_text(strip=True)
                price_text = cols[2].get_text(strip=True)
                
                fuel_type = fuel_type.replace('Бензин', '').replace('преміум', '').strip()
                fuel_type = fuel_type.replace('А-', 'A-').strip() 
                
                price = price_text.replace(',', '.').replace('грн', '').strip()
                
                if price.replace('.', '').isdigit():
                    prices[fuel_type] = float(price)
        
        update_time = soup.find('div', {'class': 'idx-updatetime'})
        if update_time:
            update_text = update_time.get_text(strip=True)
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

@csrf_exempt
def update_order_date(request, order_id):
    if request.method == 'POST':
        try:
            order = Order.objects.get(id=order_id)
            data = json.loads(request.body)
            
            order.planned_date = data['planned_date']
            order.estimated_end = data['estimated_end']
            order.save()
            
            return JsonResponse({'status': 'success'})
        except Order.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Order not found'}, status=404)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)


def get_drivers(request):
    drivers = Driver.objects.filter(user=request.user).values('id', 'name', 'surname', 'phone', 'email')
    return JsonResponse(list(drivers), safe=False)

@login_required
def drivers_list(request):
    drivers = Driver.objects.filter(user=request.user)
    return render(request, 'registrationapp/drivers.html', {'drivers': drivers})

@login_required
@require_http_methods(["GET"])
def get_driver_details(request, driver_id):
    try:
        driver = Driver.objects.get(id=driver_id, user=request.user)
        return JsonResponse({
            'id': driver.id,
            'name': driver.name,
            'surname': driver.surname,
            'phone': driver.phone,
            'email': driver.email
        })
    except Driver.DoesNotExist:
        return JsonResponse({'error': 'Driver not found'}, status=404)

@login_required
@require_http_methods(["POST"])
def create_driver(request):
    try:
        data = json.loads(request.body)
        driver = Driver.objects.create(
            name=data.get('name'),
            surname=data.get('surname'),
            phone=data.get('phone'),
            email=data.get('email'),
            user=request.user
        )
        return JsonResponse({'success': True, 'driver': {
            'id': driver.id,
            'name': driver.name,
            'surname': driver.surname,
            'phone': driver.phone,
            'email': driver.email
        }})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

@login_required
@require_http_methods(["PUT"])
def update_driver(request, driver_id):
    try:
        driver = Driver.objects.get(id=driver_id, user=request.user)
        data = json.loads(request.body)
        
        if not all([data.get('name'), data.get('surname'), data.get('phone'), data.get('email')]):
            return JsonResponse({'success': False, 'error': 'Усі поля обов\'язкові'}, status=400)
        
        driver.name = data.get('name', driver.name)
        driver.surname = data.get('surname', driver.surname)
        driver.phone = data.get('phone', driver.phone)
        driver.email = data.get('email', driver.email)
        driver.save()
        
        return JsonResponse({'success': True})
    except Driver.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Водія не знайдено'}, status=404)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Невірний формат даних'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

@login_required
@require_http_methods(["DELETE"])
def delete_driver(request, driver_id):
    try:
        driver = Driver.objects.get(id=driver_id, user=request.user)
        driver.delete()
        return JsonResponse({'success': True})
    except Driver.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Driver not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)
