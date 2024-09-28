import json
import os

from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.core.paginator import Paginator
from django.http import HttpResponseNotAllowed, JsonResponse, HttpResponseForbidden, HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.contrib import messages
from django.views.decorators.cache import cache_control
from requests import HTTPError

from GameLibrary import settings
from main.forms import SteamImportForm
from main.models import UserGameLibrary, Game
from main.serializers import UserGameLibrarySerializer
from main.services import Igdb, SteamApi


def index(request):
    return render(request, "main/index.html")


def fetch_cover_small(request, cover_id):
    try:
        Igdb.save_covers(cover_id, 'small')
    except HTTPError as e:
        return HttpResponse(status=404)
    return HttpResponse(status=200)


@login_required
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def user_settings(request):
    form = SteamImportForm()
    return render(request, "main/settings.html", {"form": form})


@login_required
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def library(request):
    return render(request, "main/library.html")


@login_required
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def library_search(request):
    query = request.GET.get("query")
    sort = request.GET.get("sort")
    order = int(request.GET.get("order", 0))
    min_rating = request.GET.get("min_rating")
    min_hours = request.GET.get("min_hours")
    status = request.GET.get("status")
    page_number = request.GET.get("page", "1")

    lib = UserGameLibrary.objects.advanced_search(request.user.id, query, sort, order, min_rating, min_hours, status)
    paginator = Paginator(lib, settings.GLOBAL_SETTINGS['LIBRARY_DEFAULT_PAGE_SIZE'])
    page = paginator.get_page(page_number)
    serializer = UserGameLibrarySerializer(page.object_list, many=True)
    return JsonResponse({
        'items': serializer.data,
        'num_pages': paginator.num_pages,
    })


@login_required
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def library_import(request):
    if request.method != "POST":
        return HttpResponseForbidden
    url = request.POST.get("url")
    return JsonResponse(UserGameLibrary.objects.import_library(request.user.id, url))


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

    cached_page = cache.get(f'search_{query}_page_{page_number}')
    if cached_page:
        return JsonResponse(cached_page)

    games = Game.games.search(query)
    paginator = Paginator(games.values('id', 'name', 'image_id').order_by('-relevance'),
                          settings.GLOBAL_SETTINGS['MAX_GAMES_PER_PAGE'])

    if games.count() != 0 and page_number <= paginator.num_pages:
        page = paginator.get_page(str(page_number))
        items = list(page.object_list)
    else:
        items = Game.games.search_api_excluding(query, games)

    if len(items) == 0:
        response = {
            'items': [],
            'has_next': False
        }
    else:
        response = {
            'items': items,
            'has_next': True
        }
    cache.set(f'search_{query}_page_{page_number}', response, timeout=60 * 15)
    return JsonResponse(response)


def game(request, game_id):
    game = get_object_or_404(Game, pk=game_id)
    context = {"game": game}

    if game.image_id is not None and not os.path.exists(f"./static/covers/big_{game.image_id}.jpg"):
        Igdb.save_covers(game.image_id, "big")

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
    if request.method != "PUT":
        return HttpResponseNotAllowed(['PUT'])
    if not request.user.is_authenticated:
        return redirect(reverse("login"))

    try:
        data = json.loads(request.body)
        playing = data.get('playing', False)
        completed = data.get('completed', False)
        retired = data.get('retired', False)
        UserGameLibrary.objects.update_library(request.user.id, game_id, data.get('review'), data.get('rating'),
                                               data.get('hours_played'), data.get('num_completions'), playing,
                                               completed,
                                               retired)
        return HttpResponse(status=200)
    except:
        return HttpResponse(status=403)


def game_delete(request, game_id):
    if request.method != "POST":
        return HttpResponseNotAllowed(['POST'])
    if not request.user.is_authenticated:
        return redirect(reverse("login"))

    UserGameLibrary.objects.delete_library(request.user.id, game_id)
    return redirect(reverse("main:game", args=[game_id]))
