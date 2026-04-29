from django.core.cache import cache
from django.db.models import Count
from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from .algorithms import (
    build_preference_graph,
    get_recommendations,
    get_recommendations_from_cache,
    cache_recommendations,
    get_pagerank_scores
)
from .models import User, Item, Interaction

# ОШИБКА БЫЛА ТУТ: Переменная не была определена
REDIS_RECOMMENDATIONS_PREFIX = 'recommendations_'


@require_GET
def get_user_recommendations_api(request, user_id: int):
    """
    API для получения рекомендаций для конкретного пользователя.
    """
    try:
        user = User.objects.get(pk=user_id) # Используйте get() вместо get_object_or_404 если хотите свой ответ
    except User.DoesNotExist:
        return JsonResponse({"error": f"User with id {user_id} not found"}, status=404)

    # Проверяем кэш
    cached_recs = get_recommendations_from_cache(user_id)
    if cached_recs:
        print(f"Recommendations for user {user_id} found in cache.")
        return JsonResponse({"user_id": user_id, "recommendations": cached_recs})
    else:
        print(f"Recommendations for user {user_id} not found in cache. Building graph and recommendations...")
        # Построение графа может быть долгим.
        # Если это долгая операция, рассмотрите ее запуск в Celery task.
        try:
            graph = build_preference_graph()
            recommendations = get_recommendations(user_id, graph=graph)

            # Кэшируем результат
            cache_recommendations(user_id, recommendations)
            print(f"Recommendations generated and cached for user {user_id}.")
            return JsonResponse({"user_id": user_id, "recommendations": recommendations})
        except Exception as e:
            print(f"Error generating recommendations for user {user_id}: {e}")
            return JsonResponse({"error": "Could not generate recommendations"}, status=500)


@csrf_exempt # В продакшене используйте Django-specific CSRFexempt или правильную обработку CSRF
@require_POST
def add_user_preference(request):
    """
    API для добавления или обновления взаимодействия пользователя с элементом.
    """
    user_id = request.POST.get('user_id')
    item_id = request.POST.get('item_id')
    interaction_type = request.POST.get('interaction_type', 'view') # По умолчанию "просмотр"

    if not user_id or not item_id:
        return JsonResponse({"error": "user_id and item_id are required"}, status=400)

    try:
        user = User.objects.get(pk=user_id)
        item = Item.objects.get(pk=item_id)

        # Используем get_or_create для добавления нового взаимодействия или получения существующего
        # Если нужно обновлять timestamp при каждом добавлении, используйте .update() внутри get_or_create
        interaction, created = Interaction.objects.get_or_create(
            user=user,
            item=item,
            interaction_type=interaction_type,
            defaults={
                'timestamp': timezone.now()
            }
        )

        # Если объект уже существовал, но мы хотим обновить timestamp
        if not created:
            interaction.timestamp = timezone.now()
            interaction.save()
            print(f"Interaction updated for user {user_id}, item {item_id}, type {interaction_type}.")
        else:
            print(f"New interaction created for user {user_id}, item {item_id}, type {interaction_type}.")

        # Очищаем кэш рекомендаций для этого пользователя, так как граф мог измениться
        # Это важно для получения актуальных рекомендаций
        cache_key = f'{REDIS_RECOMMENDATIONS_PREFIX}{user_id}'
        # r.delete(cache_key) # Если используете прямую redis-cli
        cache.delete(cache_key) # Если используете Django cache
        print(f"Cleared cache for user {user_id} due to new interaction.")

        return JsonResponse({"message": "Preference added/updated successfully", "created": created})

    except User.DoesNotExist:
        return JsonResponse({"error": f"User with id {user_id} not found"}, status=404)
    except Item.DoesNotExist:
        return JsonResponse({"error": f"Item with id {item_id} not found"}, status=404)
    except Exception as e:
        print(f"An unexpected error occurred in add_user_preference: {e}")
        return JsonResponse({"error": "An internal error occurred"}, status=500)


@require_GET
def get_graph_stats_api(request):
    """
    API для возврата общей статистики по графу.
    """
    try:
        graph = build_preference_graph()
        num_nodes = graph.number_of_nodes()
        num_edges = graph.number_of_edges()

        pagerank_scores = get_pagerank_scores(graph)
        # Топ 5 узлов по PageRank. Убираем "user_" и "item_" из меток для лучшего вывода.
        top_pagerank_nodes = []
        if pagerank_scores:
            # Сортируем сразу по значениям, а потом обрабатываем метки
            sorted_scores = sorted(pagerank_scores.items(), key=lambda item: item[1], reverse=True)
            for node_id, score in sorted_scores[:5]:
                node_type = "unknown"
                label = node_id
                if node_id.startswith("user_"):
                    node_type = "user"
                    label = node_id[5:] # Убираем "user_"
                elif node_id.startswith("item_"):
                    node_type = "item"
                    label = node_id[5:] # Убираем "item_"

                top_pagerank_nodes.append({"id": label, "type": node_type, "score": score})


        return JsonResponse({
            "num_nodes": num_nodes,
            "num_edges": num_edges,
            "top_pagerank_nodes": top_pagerank_nodes
        })
    except Exception as e:
        print(f"Error getting graph stats: {e}")
        return JsonResponse({"error": "Could not retrieve graph statistics"}, status=500)


# --- Представления для рендеринга HTML-страниц ---

def home(request):
    """
    Отображает главную страницу с пользователями и элементами.
    """
    # Оптимизация: Предполагаем, что эти списки не огромные.
    # Если списки очень большие, пагинация или выборка только необходимых полей.
    users = User.objects.only('id', 'username').all()
    items = Item.objects.only('id', 'name').all()
    context = {
        'users': users,
        'items': items
    }
    return render(request, 'recommender/home.html', context)


def graph_stats_view(request):
    """
    Отображает страницу со статистикой графа.
    """
    try:
        graph = build_preference_graph()
        num_nodes = graph.number_of_nodes()
        num_edges = graph.number_of_edges()

        pagerank_scores = get_pagerank_scores(graph)
        top_pagerank_nodes = []
        if pagerank_scores:
             sorted_scores = sorted(pagerank_scores.items(), key=lambda item: item[1], reverse=True)
             for node_id, score in sorted_scores[:5]:
                node_type = "unknown"
                label = node_id
                if node_id.startswith("user_"):
                    node_type = "user"
                    label = node_id[5:]
                elif node_id.startswith("item_"):
                    node_type = "item"
                    label = node_id[5:]
                top_pagerank_nodes.append({"id": label, "type": node_type, "score": score})

        # Получить популярные элементы (например, по идентификатору, если нет лучшего поля)
        # Аннотируем количество взаимодействий, чтобы определить популярные элементы.
        popular_items = Item.objects.annotate(
            num_interactions=Count('interaction') # Предполагается, что у Item есть обратная связь 'interaction'
        ).order_by('-num_interactions').only('id', 'name', 'num_interactions')[:5]

        context = {
            "num_nodes": num_nodes,
            "num_edges": num_edges,
            "top_pagerank_nodes": top_pagerank_nodes,
            "popular_items": popular_items
        }
        return render(request, 'recommender/stats.html', context)
    except Exception as e:
        print(f"Error rendering graph_stats_view: {e}")
        # Можно отобразить страницу с ошибкой или пустой контекст
        return render(request, 'recommender/stats.html', {"error": "Could not load statistics"})