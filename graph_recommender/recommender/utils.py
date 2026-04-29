from django.core.mail import send_mail
from django.conf import settings


def send_inactivity_reminder_email(user_email: str):
    """
    Отправляет email-напоминание пользователю о его недавней неактивности.
    """
    subject = "Мы скучаем по вам!"
    message = (
        f"Привет!\n\n"
        f"Давно не виделись. Хотите посмотреть, что нового появилось?\n"
        f"У нас есть много интересных товаров, которые могут вас заинтересовать.\n\n"
        f"Переходите по ссылке, чтобы узнать больше:\n"
        f"{settings.SITE_URL}/discover/\n\n" # Предполагаем, что есть ссылка для открытия
        f"С уважением,\n"
        f"Команда вашего сервиса"
    )
    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user_email],
            fail_silently=False,
        )
        print(f"Inactivity reminder email sent to {user_email}.")
    except Exception as e:
        print(f"Error sending inactivity email to {user_email}: {e}")

# Можно добавить и другие утилиты, например, для популярных товаров:
def send_popular_items_email(user_email: str, popular_items_names: list):
    subject = "Новые популярные товары, которые вам могут понравиться!"
    items_list_str = "\n".join([f"- {item}" for item in popular_items_names])
    message = (
        f"Привет!\n\n"
        f"Посмотрите на подборку популярных товаров, которые могут вам понравиться:\n\n"
        f"{items_list_str}\n\n"
        f"Переходите по ссылке, чтобы узнать больше:\n"
        f"{settings.SITE_URL}/items/\n\n"
        f"С уважением,\n"
        f"Команда вашего сервиса"
    )
    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user_email],
            fail_silently=False,
        )
        print(f"Popular items email sent to {user_email} for items: {', '.join(popular_items_names)}.")
    except Exception as e:
        print(f"Error sending popular items email to {user_email}: {e}")