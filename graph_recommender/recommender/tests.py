from django.test import TestCase
from .models import User, Item, Interaction
from .algorithms import build_preference_graph, get_collaborative_filtering_recommendations, get_knn_recommendations
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
        recommendations = get_collaborative_filtering_recommendations(graph, self.user1.id, num_recommendations=1)
        self.assertEqual(recommendations, [self.item3.id])

    def test_knn_recommendations(self):
        graph = build_preference_graph()
        # Если user1 любит item1, то item2 (связан user1) и item3 (связан user2, который связан с item1)
        # Предположим, что item1 -> item2 (через user1), item1 -> item3 (через user2 -> item1)
        # Алгоритм KNN находит ближайшие элементы к "любимому" элементу
        # Если любимый item1, то соседи: item2 (через user1), item3 (через user2)
        recommendations = get_knn_recommendations(graph, self.item1.id, k=2, num_recommendations=2)
        # Порядок может зависеть от конкретной реализации метрик схожести
        self.assertIn(self.item2.id, recommendations)
        self.assertIn(self.item3.id, recommendations)

