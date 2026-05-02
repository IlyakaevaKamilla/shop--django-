from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

from product.models import User

admin = User.objects.get(is_staff=True)


def send_email_admin(order, selected_items):
    html_content = render_to_string(
        'emails/admin_message.html',
        context={
            'created_at': order.created_at,
            'order_id': order.id,
            'selected_items': selected_items,
            'total_price': order.total_price,
            'first_name': order.first_name,
            'last_name': order.last_name,
            'email': order.email,
            'phone': order.phone
        },
    )
    message = EmailMultiAlternatives(
        subject=f'Новый заказ №{order.id}',
        body='',
        to=[admin.email],
    )
    message.attach_alternative(html_content, 'text/html')
    message.send()
