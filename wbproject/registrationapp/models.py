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
    amount = models.IntegerField(default=1)
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE)

    def __str__(self):
        return self.name   
    

class Vehicle(models.Model):
    name = models.CharField(max_length=255)
    capacity = models.DecimalField(max_digits=10, decimal_places=1)
    fuel_amount = models.DecimalField(max_digits=10, decimal_places=2)
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE)

    def __str__(self):
        return self.name
    
class Order(models.Model):
    name = models.CharField(max_length=255)
    destination = models.CharField(max_length=255)
    starting_point = models.CharField(max_length=255)
    STATUS_CHOICES = (
        (0, 'Pending'),
        (1, 'In Progress'),
        (2, 'Completed'),
    )
    status = models.IntegerField(choices=STATUS_CHOICES, default=0)
    priority = models.PositiveSmallIntegerField(default=1, validators=[MaxValueValidator(100)])
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return f"Order: {self.name} - {self.get_status_display()}"
    
class Order_product(models.Model):
    name = models.CharField(max_length=255)
    weight = models.DecimalField(max_digits=10, decimal_places=2)
    amount = models.IntegerField(default=1)
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE)
    order = models.ForeignKey(Order, on_delete=models.CASCADE)

    def __str__(self):
        return self.name   
    
class Order_vehicle(models.Model):
    name = models.CharField(max_length=255)
    capacity = models.DecimalField(max_digits=10, decimal_places=1)
    fuel_amount = models.DecimalField(max_digits=10, decimal_places=2)
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE)
    order = models.ForeignKey(Order, on_delete=models.CASCADE)

    def __str__(self):
        return self.name   
    
