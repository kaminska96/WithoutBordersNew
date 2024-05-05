from django.shortcuts import render
from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from django.contrib import messages, auth
from withoutborders.models import Profile
from django.contrib import auth
from django.http import JsonResponse
from .models import Warehouse
from django.views.decorators.csrf import csrf_exempt
import json


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
    return render(request, 'registrationapp/main.html')

def main2(request):
    return render(request, 'registrationapp/main2.html')

def main3(request):
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
