from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MaxValueValidator

User = get_user_model()


class Warehouse(models.Model):
    name = models.CharField(max_length=255)
    location = models.CharField(max_length=255)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.name} - {self.location}"
    

class Product(models.Model):
    name = models.CharField(max_length=255)
    weight = models.DecimalField(max_digits=10, decimal_places=2)
    amount = models.IntegerField(default=0)
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE)

    def __str__(self):
        return self.name   
    

class Vehicle(models.Model):
    FUEL_TYPE_CHOICES = [
        ('Бензин А-95 преміум', 'Бензин А-95 преміум'),
        ('Бензин А-95', 'Бензин А-95'),
        ('Бензин А-92', 'Бензин А-92'),
        ('Дизельне паливо', 'Дизельне паливо'),
        ('Газ автомобільний', 'Газ автомобільний'),
    ]
    
    name = models.CharField(max_length=255)
    capacity = models.DecimalField(max_digits=10, decimal_places=1)
    fuel_amount = models.DecimalField(max_digits=10, decimal_places=2)
    fuel_type = models.CharField(
        max_length=50,
        choices=FUEL_TYPE_CHOICES,
        default='Бензин А-95'
    )
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE)
    
    def __str__(self):
        return self.name
    
class Order(models.Model):
    name = models.CharField(max_length=255)
    STATUS_CHOICES = (
        (0, 'Pending'),
        (1, 'In Progress'),
        (2, 'Completed'),
    )
    reminder_sent = models.BooleanField(default=False)
    driver_reminder_sent = models.BooleanField(default=False)
    status = models.IntegerField(choices=STATUS_CHOICES, default=0)
    priority = models.PositiveSmallIntegerField(default=1, validators=[MaxValueValidator(100)])
    planned_date = models.DateTimeField(blank=True, null=True)
    estimated_end = models.DateTimeField(blank=True, null=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return f"Order: {self.name} - {self.get_status_display()}"
    
    
class Order_vehicle(models.Model):
    FUEL_TYPE_CHOICES = [
        ('Бензин А-95 преміум', 'Бензин А-95 преміум'),
        ('Бензин А-95', 'Бензин А-95'),
        ('Бензин А-92', 'Бензин А-92'),
        ('Дизельне паливо', 'Дизельне паливо'),
        ('Газ автомобільний', 'Газ автомобільний'),
    ]

    name = models.CharField(max_length=255)
    capacity = models.DecimalField(max_digits=10, decimal_places=1)
    fuel_amount = models.DecimalField(max_digits=10, decimal_places=2)
    fuel_type = models.CharField(
        max_length=50,
        choices=FUEL_TYPE_CHOICES,
        default='Бензин А-95'
    )
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE)
    order = models.ForeignKey(Order, on_delete=models.CASCADE)

    def __str__(self):
        return self.name   
    
class Order_destinations(models.Model):
    destination = models.CharField(max_length=255)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='order_destinations')

    def __str__(self):
        return self.destination
        

class Order_warehouses(models.Model):
    warehouse_location = models.CharField(max_length=255)
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='order_warehouses')

    def __str__(self):
        return self.warehouse_location  

class Order_product(models.Model):
    name = models.CharField(max_length=255)
    weight = models.DecimalField(max_digits=10, decimal_places=2)
    amount = models.IntegerField(default=1)
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE)
    order_destinations = models.ForeignKey(Order_destinations, on_delete=models.CASCADE)

    def __str__(self):
        return self.name

from django.db import models

class Driver(models.Model):
    name = models.CharField(max_length=100)
    surname = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)
    email = models.CharField(max_length=255)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.name

class Order_driver(models.Model):
    name = models.CharField(max_length=100)
    surname = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)
    email = models.CharField(max_length=255)
    order_vehicle = models.ForeignKey(Order_vehicle, on_delete=models.CASCADE)

    def __str__(self):
        return self.name
