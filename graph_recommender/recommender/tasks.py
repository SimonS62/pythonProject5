from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from . import models
from .models import User, Interaction
from .utils import send_inactivity_reminder_email, send_popular_items_email


@shared_task
def check_user_inactivity_task():
    """
    Задача Celery для поиска неактивных пользователей и отправки им напоминаний.
    """
    if User is None or Interaction is None or send_inactivity_reminder_email is None:
        print("Required modules (User, Interaction, send_inactivity_reminder_email) not available. Skipping task.")
        return {'status': 'error', 'message': 'Dependencies not met'}

    print("Starting check_user_inactivity_task...")
    now = timezone.now()
    inactivity_threshold_days = 30 # Пользователь считается неактивным, если не было взаимодействий за 30 дней
    inactivity_threshold = timezone.now() - timedelta(days=inactivity_threshold_days)
    users_reminded_count = 0

    # 1. Находим всех пользователей
    all_users = User.objects.all()

    for user in all_users:
        # 2. Проверяем дату последнего взаимодействия для каждого пользователя
        last_interaction = Interaction.objects.filter(user=user).order_by('-timestamp').first()

        if last_interaction:
            if last_interaction.timestamp < inactivity_threshold:
                # Пользователь неактивен
                try:
                    send_inactivity_reminder_email(user.username) # Предполагаем, что у User есть поле email, если нет, замените на username или другое поле
                    users_reminded_count += 1
                except Exception as e:
                    print(f"Failed to send inactivity reminder to user {user.username}: {e}")
        else:
            # Пользователь никогда не совершал взаимодействий
            # Можно добавить логику для отправки приветственного письма или упустить таких пользователей
            print(f"User {user.username} has no interactions yet. Skipping inactivity check.")

    print(f"Finished check_user_inactivity_task. Sent {users_reminded_count} inactivity reminders.")

    return {
        'status': 'success',
        'users_reminded': users_reminded_count,
        'timestamp': now.isoformat()
    }

# --- Пример другой задачи: Отправка уведомлений о популярных товарах ---

@shared_task
def send_popular_items_to_users_task():
    """
    Задача для определения популярных товаров и отправки их пользователям.
    """
    if User is None or Interaction is None or send_popular_items_email is None:
        print("Required modules (User, Interaction, send_popular_items_email) not available. Skipping task.")
        return {'status': 'error', 'message': 'Dependencies not met'}

    print("Starting send_popular_items_to_users_task...")
    now = timezone.now()
    recent_interactions_threshold = now - timedelta(days=7) # Товары, популярные за последнюю неделю
    min_interactions_for_popularity = 10 # Минимальное количество взаимодействий, чтобы считать товар популярным

    # 1. Находим популярные товары за последнюю неделю
    popular_items_data = Interaction.objects.filter(
        timestamp__gte=recent_interactions_threshold
    ).values('item__name').annotate(interaction_count=models.Count('item__name')).order_by('-interaction_count')

    popular_items = [
        item['item__name'] for item in popular_items_data
        if item['interaction_count'] >= min_interactions_for_popularity
    ][:5] # Берем топ-5 популярных товаров

    if not popular_items:
        print("No popular items found in the last week. Skipping task.")
        return {'status': 'skipped', 'message': 'No popular items'}

    print(f"Found popular items: {popular_items}")

    # 2. Находим пользователей, которые могут быть заинтересованы (например, активные пользователи)
    # Для простоты, отправим всем пользователям, которые были активны за последнюю неделю
    active_users_emails = User.objects.filter(
        interactions__timestamp__gte=recent_interactions_threshold
    ).distinct().values_list('username', flat=True) # Предполагается, что username является email, если нет, то нужно поле email

    users_notified_count = 0
    for user_email in active_users_emails:
        try:
            send_popular_items_email(user_email, popular_items)
            users_notified_count += 1
        except Exception as e:
            print(f"Failed to send popular items email to {user_email}: {e}")

    print(f"Finished send_popular_items_to_users_task. Sent popular items notification to {users_notified_count} users.")

    return {
        'status': 'success',
        'popular_items_found': len(popular_items),
        'users_notified': users_notified_count,
        'timestamp': now.isoformat()
    }