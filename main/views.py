from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, Page
from django.db.models import Q
from django.shortcuts import render

from GameLibrary import settings
from main.models import UserGameLibrary, Game
from .services import Igdb


# Create your views here.
def index(request):
    return render(request, "main/index.html")


@login_required
def library(request):
    # TODO: paging
    games = UserGameLibrary.objects.filter(user=request.user)
    context = {"games": games}
    return render(request, "main/library.html", context)


def search(request):
    query = request.GET.get("query")
    context = {"query": query}

    if query is None:
        return render(request, "main/search_games.html", context)

    if query is not None and len(query.strip()) <= 3:
        context.update({"error_length": True})
        return render(request, "main/search_games.html", context)

    # TODO: cache
    games = Game.games.search(query)
    paginator = Paginator(games, settings.GLOBAL_SETTINGS['MAX_GAMES_PER_PAGE'])
    page_number = request.GET.get("page")
    if page_number is None:
        page_number = 1
    page_obj = paginator.get_page(page_number)

    if games.count() == 0 or int(page_number) == paginator.num_pages:
        context.update({"show_api_button": True})

    api_search = request.GET.get("api_search")
    if api_search or games.count() == 0:
        games_api = Game.games.search_api_excluding(query, games)
        page_obj = Page(games_api, paginator.num_pages if games.count() == 0 else paginator.num_pages+1, paginator)

    context.update({"page_obj": page_obj})
    return render(request, "main/search_games.html", context)
