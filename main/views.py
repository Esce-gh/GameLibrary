from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import HttpResponseNotAllowed, JsonResponse, HttpResponseForbidden
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
    if query is not None and len(query.strip()) < 3:
        context = {"error_length": True}
    else:
        context = {"query": query}
    return render(request, "main/search_games.html", context)


def ajax_search(request):
    query = request.GET.get("query")
    if len(query.strip()) < 3:
        return HttpResponseForbidden()
    page_number = int(request.GET.get("page", 1))
    games = Game.games.search(query)  # TODO: order by and cache
    paginator = Paginator(games.values('id', 'name', 'image_id').order_by('-relevance'), settings.GLOBAL_SETTINGS['MAX_GAMES_PER_PAGE'])
    if games.count() != 0 and page_number <= paginator.num_pages:
        page = paginator.get_page(str(page_number))
        items = list(page.object_list)

        return JsonResponse({
            'items': items,
            'has_next': True,
        })

    games_api = Game.games.search_api_excluding(query, games)

    if len(games_api) == 0:
        return JsonResponse({
            'items': [],
            'has_next': False
        })

    return JsonResponse({
        'items': games_api,
        'has_next': True
    })


def game(request, game_id):
    context = {"game": get_object_or_404(Game, id=game_id)}

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
