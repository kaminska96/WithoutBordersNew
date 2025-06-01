from django.core.management.base import BaseCommand
from django.core.mail import send_mail, BadHeaderError
from django.template.loader import render_to_string
from django.utils import timezone
from datetime import timedelta
from smtplib import SMTPException
from registrationapp.models import Order  # adjust if your model is elsewhere

class Command(BaseCommand):
    help = 'Send reminder emails for orders planned 24 hours from now'

    def handle(self, *args, **kwargs):
        now = timezone.now()
        in_24_hours = now + timedelta(hours=24)
        time_margin = timedelta(minutes=30)
        
        # Find orders scheduled ~24h from now
        orders = Order.objects.filter(
            planned_date__gte=in_24_hours - time_margin,
            planned_date__lte=in_24_hours + time_margin,
            status=0,  # Pending
            reminder_sent=False  # Only send once
        )

        if not orders.exists():
            self.stdout.write("No reminders to send at this time.")
            return

        success_count = 0
        fail_count = 0

        for order in orders:
            try:
                self.send_reminder(order)
                order.reminder_sent = True
                order.save()
                success_count += 1
                self.stdout.write(f"Reminder sent to {order.user.email} for order {order.name}")
            except (BadHeaderError, SMTPException) as e:
                self.stdout.write(self.style.ERROR(
                    f'Failed to send reminder for order {order.id}: {str(e)}'
                ))
                fail_count += 1

        self.stdout.write(self.style.SUCCESS(
            f'Successfully sent {success_count} reminders. Failed: {fail_count}'
        ))

    def send_reminder(self, order):
        subject = f'Нагадування про замовлення: {order.name}'
        context = {
            'order': order,
            'planned_date': order.planned_date.strftime('%Y-%m-%d %H:%M'),
        }
        
        html_message = render_to_string('emails/order_reminder.html', context)
        plain_message = render_to_string('emails/order_reminder.txt', context)

        send_mail(
            subject=subject,
            message=plain_message,
            from_email=None,  # Uses DEFAULT_FROM_EMAIL from settings
            recipient_list=[order.user.email],
            html_message=html_message,
            fail_silently=False,
        )