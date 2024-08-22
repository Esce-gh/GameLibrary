from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, Page
from django.http import HttpResponseBadRequest, HttpResponseNotFound, HttpResponseNotAllowed, HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.contrib import messages
from GameLibrary import settings
from main.models import UserGameLibrary, Game


# Create your views here.
def index(request):
    return render(request, "main/index.html")


@login_required
def library(request):
    # TODO: paging
    user_library = UserGameLibrary.objects.get_user_library(request.user.id)
    context = {"library": user_library}
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
        if len(games_api) != 0:
            page_obj = Page(games_api, paginator.num_pages if games.count() == 0 else paginator.num_pages+1, paginator)
        else:
            context.update({'error_api_results': True})

    context.update({"page_obj": page_obj})
    return render(request, "main/search_games.html", context)


def game(request, game_id):
    context = {"game": get_object_or_404(Game, igdb_id=game_id)}

    if request.user.is_authenticated:
        user_entry = UserGameLibrary.objects.get_library_entry(request.user.id, game_id)
        context.update({'user_entry': user_entry})

    return render(request, "main/game.html", context)


def game_add(request, game_id):
    if request.method != "POST":
        return HttpResponseNotAllowed(['POST'])
    if not request.user.is_authenticated:
        return redirect(reverse("login"))

    if UserGameLibrary.objects.save_library(request.user.id, game_id):
        messages.success(request, "Game was successfully saved.")
    else:
        messages.error(request, "Game was not successfully saved.")
    return redirect(reverse("main:game", args=[game_id]))


def game_edit(request, game_id):
    if request.method != "POST":
        return HttpResponseNotAllowed(['POST'])
    if not request.user.is_authenticated:
        return redirect(reverse("login"))

    if UserGameLibrary.objects.update_library(request.user.id, game_id, request.POST['review'], request.POST['rating']):
        messages.success(request, "Game successfully updated")
    else:
        messages.error(request, "Unable to update game")
    return redirect(reverse("main:game", args=[game_id]))


def game_delete(request, game_id):
    if request.method != "POST":
        return HttpResponseNotAllowed(['POST'])
    if not request.user.is_authenticated:
        return redirect(reverse("login"))

    UserGameLibrary.objects.delete_library(request.user.id, game_id)
    return redirect(reverse("main:game", args=[game_id]))
