from django.core.cache import cache
import json
import networkx as nx
from .models import User, Item, Interaction


def get_recommendations_from_cache(user_id: int):
    """Получает рекомендации из кэша."""
    cache_key = f'recommendations_{user_id}'
    cached_data = cache.get(cache_key)

    # 1. Сначала проверяем, что данные вообще есть
    if cached_data is None:
        return None

    # 2. Добавляем try, чтобы перехватить ошибку, если в кэше лежит "мусор"
    try:
        return json.loads(cached_data)
    except (json.JSONDecodeError, TypeError):
        # Если данные в кэше битые, возвращаем None
        return None

def cache_recommendations(user_id: int, recommendations):
    """Кэширует рекомендации."""
    cache_key = f'recommendations_{user_id}' # Или используйте ваш префикс
    try:
        # Сохраняем как JSON строку для универсальности
        cache.set(cache_key, json.dumps(recommendations), timeout=3600) # Время жизни кэша - 1 час
    except Exception as e:
        print(f"Error caching recommendations for user {user_id}: {e}")

# --- Основные алгоритмы ---

def build_preference_graph() -> nx.Graph:
    """
    Строит граф предпочтений пользователей и элементов.
    """
    G = nx.Graph()

    # Добавляем узлы пользователей
    users = User.objects.only('id', 'username').all()
    for user in users:
        G.add_node(f"user_{user.id}", type='user', label=user.username)

    # Добавляем узлы элементов
    items = Item.objects.only('id', 'name').all()
    for item in items:
        G.add_node(f"item_{item.id}", type='item', label=item.name)

    # Добавляем ребра взаимодействий
    interactions = Interaction.objects.select_related('user', 'item').all()
    for interaction in interactions:
        user_node = f"user_{interaction.user.id}"
        item_node = f"item_{interaction.item.id}"
        # Можно добавить вес ребра в зависимости от interaction_type или его частоты
        # Для простоты, пока вес 1
        weight = 1
        if G.has_edge(user_node, item_node):
            G[user_node][item_node]['weight'] += weight
        else:
            G.add_edge(user_node, item_node, weight=weight, type=interaction.interaction_type)

    print(f"Graph built with {G.number_of_nodes()} nodes and {G.number_of_edges()} edges.")
    return G

def get_recommendations(user_id: int, graph: nx.Graph) -> list[str]:
    """
    Генерирует рекомендации для пользователя на основе графа.
    Простая реализация - возвращает "соседей" пользователя, которые еще не были просмотрены.
    """
    user_node = f"user_{user_id}"
    recommendations = []

    if user_node not in graph:
        print(f"User node {user_node} not found in graph.")
        return []

    # Получаем элементы, с которыми взаимодействовал пользователь
    user_interactions = set(neighbor for neighbor in graph.neighbors(user_node) if neighbor.startswith('item_'))

    # Получаем все элементы (узлы типа 'item')
    all_items_in_graph = {node for node, data in graph.nodes(data=True) if data.get('type') == 'item'}

    # Элементы, которые пользователь еще не видел (или не взаимодействовал)
    # В более сложной логике здесь может быть фильтрация по типу взаимодействия
    recommended_items_to_consider = list(all_items_in_graph - user_interactions)

    # Простая сортировка по PageRank (если есть) или случайным образом
    # Для этой простой реализации, просто вернем список, который потом будет отсортирован
    # Или можно найти общих соседей с другими пользователями.
    # Здесь будет ваша более сложная логика рекомендаций
    # Например, можно использовать PageRank для определения важности узлов
    try:
        pagerank_scores = nx.pagerank(graph, alpha=0.85) # alpha - параметр затухания
        # Фильтруем и сортируем рекомендованные элементы
        sorted_recommendations = sorted(
            [(item_node, pagerank_scores.get(item_node, 0)) for item_node in recommended_items_to_consider],
            key=lambda x: x[1],
            reverse=True
        )
        # Возвращаем только ID элементов
        recommendations = [item_id for item_id, score in sorted_recommendations[:10]] # Топ 10 рекомендаций
        print(f"Generated recommendations for user {user_id}: {recommendations}")
    except nx.PowerIterationFailedConvergence:
        print(f"PageRank did not converge for user {user_id}. Returning raw list.")
        # Если PageRank не сходится, просто вернем список, возможно, без сортировки
        recommendations = recommended_items_to_consider[:10] # Первые 10 элементов

    return recommendations

def get_pagerank_scores(graph: nx.Graph):
    """
    Вычисляет PageRank для всех узлов графа.
    """
    try:
        return nx.pagerank(graph, alpha=0.85)
    except nx.PowerIterationFailedConvergence:
        print("PageRank calculation failed to converge. Returning empty scores.")
        return {}
    except Exception as e:
        print(f"An error occurred during PageRank calculation: {e}")
        return {}