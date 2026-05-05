from django.core.management.base import BaseCommand
from ...models import Item, UserPreference, Recommendation
from django.utils import timezone
import random
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = 'Заполняет БД тестовыми данными'

    def handle(self, *args, **options):
        self.stdout.write('Заполнение БД тестовыми данными...')

        # === 1. СОЗДАНИЕ СУПЕРПОЛЬЗОВАТЕЛЯ (АДМИНА) ===
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser('admin', 'admin@test.com', 'admin123')
            self.stdout.write(self.style.SUCCESS('Создан суперпользователь: admin / admin123'))
        else:
            self.stdout.write('Суперпользователь admin уже существует.')

        # Создаем пользователей
        users = []
        for i in range(5):
            user, created = User.objects.get_or_create(
                username=f'test_user_{i}',
                defaults={
                    'email': f'user{i}@test.com',
                    'first_name': f'User_{i}'
                }
            )
            if created:
                user.set_password('testpass123')
                user.save()
            users.append(user)

        # Создаем элементы
        items_data = [
            {'name': 'Товар A', 'category': 'Электроника'},
            {'name': 'Товар B', 'category': 'Одежда'},
            {'name': 'Товар C', 'category': 'Книги'},
            {'name': 'Товар D', 'category': 'Электроника'},
            {'name': 'Товар E', 'category': 'Спорт'},
        ]

        items = []
        for item_data in items_data:
            category_val = item_data.get('category', 'Default')

            item, _ = Item.objects.get_or_create(
                name=item_data['name'],
                defaults={
                    'category': category_val
                }
            )
            items.append(item)

        # Создаем предпочтения
        for user in users:
            random_items = random.sample(items, 2)
            for item in random_items:
                UserPreference.objects.get_or_create(
                    user=user,
                    item=item,
                    defaults={
                        'rating': random.randint(1, 5),
                        'created_at': timezone.now()
                    }
                )

        # Создаем рекомендации
        for user in users:
            random_items = random.sample(items, 2)
            for item in random_items:
                if not Recommendation.objects.filter(user=user, item=item).exists():
                    Recommendation.objects.create(
                        user=user,
                        item=item,
                        score=random.uniform(0.5, 1.0),
                        created_at=timezone.now()
                    )

        self.stdout.write(self.style.SUCCESS('Данные успешно добавлены!'))
