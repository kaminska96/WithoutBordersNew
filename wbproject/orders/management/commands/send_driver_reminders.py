from django.core.management.base import BaseCommand
from django.core.mail import send_mail, BadHeaderError
from django.template.loader import render_to_string
from django.utils import timezone
from datetime import timedelta
from smtplib import SMTPException
from registrationapp.models import Order, Order_vehicle, Order_driver 

class Command(BaseCommand):
    help = 'Send reminder emails to drivers for orders starting in 1 hour'

    def handle(self, *args, **kwargs):
        now = timezone.now()
        in_1_hour = now + timedelta(hours=1)
        time_margin = timedelta(minutes=30)
        
        orders = Order.objects.filter(
            planned_date__gte=in_1_hour - time_margin,
            planned_date__lte=in_1_hour + time_margin,
            status=0, 
            driver_reminder_sent=False
        )

        if not orders.exists():
            self.stdout.write("No driver reminders to send at this time.")
            return

        success_count = 0
        fail_count = 0

        for order in orders:
            try:
                vehicles = Order_vehicle.objects.filter(order=order)
                
                for vehicle in vehicles:
                    try:
                        driver = Order_driver.objects.get(order_vehicle=vehicle)
                        self.send_driver_reminder(order, vehicle, driver)
                        success_count += 1
                    except Order_driver.DoesNotExist:
                        self.stdout.write(f"No driver assigned to vehicle {vehicle.name} for order {order.name}")
                        continue
                
                order.driver_reminder_sent = True
                order.save()
                
            except (BadHeaderError, SMTPException) as e:
                self.stdout.write(self.style.ERROR(
                    f'Failed to send driver reminder for order {order.id}: {str(e)}'
                ))
                fail_count += 1

        self.stdout.write(self.style.SUCCESS(
            f'Successfully sent {success_count} driver reminders. Failed: {fail_count}'
        ))

    def send_driver_reminder(self, order, vehicle, driver):
        subject = f'Нагадування про замовлення: {order.name}'
        
        warehouse = vehicle.warehouse
        
        context = {
            'order': order,
            'driver': driver,
            'vehicle': vehicle,
            'warehouse': warehouse,
            'planned_date': order.planned_date.strftime('%Y-%m-%d %H:%M'),
        }
        
        html_message = render_to_string('emails/driver_reminder.html', context)
        plain_message = render_to_string('emails/driver_reminder.txt', context)

        send_mail(
            subject=subject,
            message=plain_message,
            from_email=None,
            recipient_list=[driver.email],
            html_message=html_message,
            fail_silently=False,
        )