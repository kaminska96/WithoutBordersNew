# Generated by Django 5.2 on 2025-05-23 22:33

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('registrationapp', '0007_remove_order_destination_remove_order_starting_point_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='order_product',
            name='order',
        ),
        migrations.AddField(
            model_name='order_product',
            name='order_destinations',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='registrationapp.order_destinations'),
        ),
        migrations.AddField(
            model_name='order_vehicle',
            name='fuel_type',
            field=models.CharField(choices=[('Бензин А-95 преміум', 'Бензин А-95 преміум'), ('Бензин А-95', 'Бензин А-95'), ('Бензин А-92', 'Бензин А-92'), ('Дизельне паливо', 'Дизельне паливо'), ('Газ автомобільний', 'Газ автомобільний')], default='Бензин А-95', max_length=50),
        ),
    ]
