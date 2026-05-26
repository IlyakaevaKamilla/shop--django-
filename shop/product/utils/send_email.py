from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

from product.models import User

admin = User.objects.get(is_staff=True)


def send_email_admin(order, selected_items):
    html_content_admin = render_to_string(
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
    html_content_user = render_to_string(
        'emails/user_message.html',
        context={
            'created_at': order.created_at,
            'first_name': order.first_name,
            'last_name': order.last_name,
            'total_price': order.total_price,
            'status': order.get_status_display(),
        }
    )
    message_to_admin = EmailMultiAlternatives(
        subject=f'Новый заказ №{order.id}',
        body='',
        to=[admin.email],
    )
    message_to_admin.attach_alternative(html_content_admin, 'text/html')
    message_to_admin.send()

    try:
        user_email = order.user.email if order.user.email else order.email
        message_to_user = EmailMultiAlternatives(
            subject='Спасибо за заказ!',
            body='',
            to=[user_email],
        )
        message_to_user.attach_alternative(html_content_user, 'text/html')
        message_to_user.send()
    except Exception as e:
        print('Ошибка при отправке письма пользователю', str(e))
