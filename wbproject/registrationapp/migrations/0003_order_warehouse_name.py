# Generated by Django 5.0.2 on 2024-05-21 09:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('registrationapp', '0002_order_product_order_vehicle'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='warehouse_name',
            field=models.CharField(default='', max_length=255),
        ),
    ]
