from django.test import TestCase, Client
from django.urls import reverse, NoReverseMatch
from django.contrib.auth.models import User
from .models import Item, UserPreference

class GraphRecommenderTests(TestCase):
    def setUp(self):
        self.user1 = User.objects.create(username="user1")
        self.user2 = User.objects.create(username="user12")

        self.item1 = Item.objects.create(name="Item 1", category="Cat1")
        self.item2 = Item.objects.create(name="Item 2", category="Cat1")
        self.item3 = Item.objects.create(name="Item 3", category="Cat1")

        UserPreference.objects.create(user=self.user1, item=self.item1, rating=5)
        UserPreference.objects.create(user=self.user1, item=self.item2, rating=4)

    def get_url(self, name, *args):
        """Вспомогательный метод для определения URL с учетом namespace"""
        try:
            return reverse(name, args=args)
        except NoReverseMatch:
            # Если в проекте используется include(..., namespace='...')
            # Попробуйте заменить 'recommender' на имя из вашего основного urls.py
            return reverse(f'recommender:{name}', args=args)

    def test_api_recommendations_status(self):
        client = Client()
        url = self.get_url('api_recommendations', self.user1.id)
        response = client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_api_add_preference(self):
        client = Client()
        url = self.get_url('api_add_preference')
        # Важно: убедитесь что ключи в словаре (user_id, item_id, rating)
        # совпадают с тем, что ожидает views.add_user_preference
        response = client.post(url, {
            'user_id': self.user1.id,
            'item_id': self.item3.id,
            'rating': 5
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(UserPreference.objects.count(), 3)

    def test_model_str(self):
        self.assertEqual(str(self.item1), "Item 1")
