from django.test import TestCase
from .models import User, Item, Interaction
from .algorithms import build_preference_graph, get_recommendations
import networkx as nx


class GraphRecommenderTests(TestCase):

    def setUp(self):
        # Создаем тестовых пользователей и элементы
        self.user1 = User.objects.create(username='user1')
        self.user2 = User.objects.create(username='user2')
        self.user3 = User.objects.create(username='user3')

        self.item1 = Item.objects.create(name='Item A')
        self.item2 = Item.objects.create(name='Item B')
        self.item3 = Item.objects.create(name='Item C')
        self.item4 = Item.objects.create(name='Item D')

        # Создаем тестовые взаимодействия
        Interaction.objects.create(user=self.user1, item=self.item1, interaction_type='view')
        Interaction.objects.create(user=self.user1, item=self.item2, interaction_type='view')
        Interaction.objects.create(user=self.user2, item=self.item1, interaction_type='view')
        Interaction.objects.create(user=self.user2, item=self.item3, interaction_type='view')
        Interaction.objects.create(user=self.user3, item=self.item2, interaction_type='view')
        Interaction.objects.create(user=self.user3, item=self.item4, interaction_type='view')

    def test_build_preference_graph(self):
        graph = build_preference_graph()
        self.assertIsInstance(graph, nx.Graph)
        self.assertEqual(graph.number_of_nodes(), 3 + 4) # 3 пользователя + 4 элемента
        self.assertEqual(graph.number_of_edges(), 6) # 6 взаимодействий

        # Проверяем наличие узлов и ребер
        self.assertIn('user_1', graph)
        self.assertIn('item_1', graph)
        self.assertTrue(graph.has_edge('user_1', 'item_1'))
        self.assertTrue(graph.has_edge('user_1', 'item_2'))

    def test_collaborative_filtering(self):
        graph = build_preference_graph()
        # user1 видел item1, item2
        # user2 видел item1, item3
        # user2 и user1 имеют общую интерес к item1
        # Ожидаем, что user2 будет рекомендован item3
        recommendations = get_recommendations(self.user1.id, graph)
        expected_item_name = f"item_{self.item3.id}"
        self.assertIn(expected_item_name, recommendations)

    def test_knn_recommendations(self):
        graph = build_preference_graph()
        recommendations = get_recommendations(self.user1.id, graph)

        # Список всех возможных товаров, которые мы создали в setUp
        possible_items = [f"item_{self.item1.id}", f"item_{self.item2.id}", f"item_{self.item3.id}"]

        # Проверяем, что хотя бы один из рекомендованных товаров входит в наш список созданных
        found = any(item in recommendations for item in possible_items)
        self.assertTrue(found, f"Recommendations {recommendations} did not contain any of our test items")

