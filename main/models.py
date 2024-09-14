import math
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models, IntegrityError
import logging
from django.db.models import F

from .services import Igdb, SteamApi

logger = logging.getLogger(__name__)


class GameManager(models.Manager):
    def search(self, query):
        return self.get_queryset().filter(name__icontains=query)

    def search_api_excluding(self, query, found_games):
        igdb_api = Igdb()
        excluded_ids = [game.id for game in found_games]
        games_api = igdb_api.extended_search(query, excluded_ids)
        self._save_games_from_json(games_api)
        return games_api

    def save_games_steam_id(self, ids):
        igdb_api = Igdb()
        new_games = []
        for i in range(math.ceil(len(ids) / 400)):
            ids_sliced = ids[i * 400:(i + 1) * 400]
            try:
                new_games.extend(igdb_api.get_games_by_steam_ids(ids_sliced))
            except Exception as e:
                logger.exception(e)
        created_games = []
        bulk_games = [
            self._create_game_object(game, created_games) for game in new_games if 'game' in game
        ]
        self.bulk_create(bulk_games, ignore_conflicts=True)
        steam_ids = {steam_id for igdb_id, steam_id in created_games}
        games_not_found = {x for x in ids if x not in steam_ids}
        return {'steam_ids_failed': games_not_found, 'games_saved': created_games}

    def _create_game_object(self, game, created_games=None):
        game_details = game['game']
        if created_games is not None:
            created_games.append((game_details['id'], int(game['uid'])))
        return Game(
            name=game_details["name"],
            id=game_details["id"],
            relevance=game_details["total_rating_count"] if "total_rating_count" in game_details else 0,
            image_id=game_details['cover']['image_id'] if 'cover' in game_details else None,
            steam_id=game['uid']
        )

    def _save_games_from_json(self, games):
        for game in games:
            try:
                if game['image_id'] is not None:
                    Igdb.save_covers(game['image_id'], "small")
                self.create(name=game["name"], id=game["id"], relevance=game["total_rating_count"],
                            image_id=game['image_id'], steam_id=game['steam_id'])
            except IntegrityError:
                logger.exception(f"Failed to save, game with {game['id']} ID already exists in database")

    def get_queryset(self):
        return super().get_queryset()


class Game(models.Model):
    name = models.CharField(max_length=100)
    id = models.IntegerField(unique=True, primary_key=True)
    relevance = models.IntegerField(default=0)
    image_id = models.CharField(max_length=100, blank=True, null=True)
    steam_id = models.IntegerField(blank=True, null=True)
    games = GameManager()

    def __str__(self):
        return self.name


class UserGameLibraryManager(models.Manager):
    def get_library_entry(self, user_id, game_id):
        return self.filter(user_id=user_id, game_id=game_id).first()

    def get_user_library(self, user_id):
        return self.filter(user_id=user_id)

    def advanced_search(self, user_id, query=None, sort=None, order=0, min_rating=None, min_hours=None, status=None):
        lib = self.get_user_library(user_id)
        if query:
            lib = lib.filter(game__name__icontains=query)
        if min_rating:
            lib = lib.filter(rating__gte=int(min_rating))
        if min_hours:
            lib = lib.filter(hours_played__gte=int(min_hours))
        if status == 'completed':
            lib = lib.filter(status_completed=True)
        elif status == 'playing':
            lib = lib.filter(status_playing=True)
        elif status == 'retired':
            lib = lib.filter(status_retired=True)
        if sort:
            if order == 1:
                lib = lib.order_by(F(f'{sort}').desc(nulls_last=True))
            else:
                lib = lib.order_by(F(f'{sort}').asc(nulls_last=True))
        else:
            lib = lib.order_by(f"game__name")
        return lib

    def save_library(self, user_id, game_id):
        try:
            self.create(user_id=user_id, game_id=game_id)
            return True
        except IntegrityError:
            logger.exception(f"Failed to save user {user_id}, game {game_id}")
            return False
        except ValidationError:
            logger.exception(f"Validation error for user {user_id}, game {game_id}")
            return False

    def update_library(self, user_id, game_id, review, rating, hours, completions, playing, completed, retired):
        try:
            entry = self.get(user_id=user_id, game_id=game_id)
            entry.review = review
            entry.rating = rating
            entry.hours_played = hours
            entry.num_completions = completions
            entry.status_playing = playing
            entry.status_completed = completed
            entry.status_retired = retired
            entry.save()
        except ValidationError as e:
            logger.exception(f"Validation error for user {user_id}, game {game_id}")
            raise e
        except UserGameLibrary.DoesNotExist as e:
            logger.exception(f"Cannot update an entry that doesn't exist. Game {game_id}, user {user_id}")
            raise e

    def delete_library(self, user_id, game_id):
        try:
            self.filter(user_id=user_id, game_id=game_id).delete()
        except IntegrityError:
            logger.exception(f"Failed to delete user {user_id}, game {game_id}")

    def import_library(self, user_id, steam_id):
        api = SteamApi()
        steam_lib = api.get_user_library(steam_id)
        if steam_lib is None:
            return {'error': 'Could not retrieve games (this account might be private)'}
        steam_ids = [x['appid'] for x in steam_lib]

        found_games = Game.games.get_queryset().filter(steam_id__in=steam_ids)
        updated_steam_ids = []

        for game in found_games:
            steam_game = next(filter(lambda x: x['appid'] == game.steam_id, steam_lib))
            updated_steam_ids.append(steam_game['appid'])
            self.update_or_create(user_id=user_id, game_id=game.id, defaults={'hours_played': steam_game['playtime_forever'] / 60})

        steam_ids = [x for x in steam_ids if x not in updated_steam_ids]
        save_response = Game.games.save_games_steam_id(steam_ids)
        for id in save_response['games_saved']:
            steam_game = next(filter(lambda x: x['appid'] == id[1], steam_lib))
            self.update_or_create(user_id=user_id, game_id=id[0], defaults={'hours_played': steam_game['playtime_forever'] / 60})
        save_errors = list(filter(lambda x: x['appid'] in save_response['steam_ids_failed'], steam_lib))
        return {'save_errors': save_errors}

    def get_queryset(self):
        return super().get_queryset()


class UserGameLibrary(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    review = models.TextField(null=True, blank=True)
    rating = models.FloatField(null=True, blank=True, validators=[MinValueValidator(1.0), MaxValueValidator(10.0)])
    hours_played = models.FloatField(null=True, blank=True, validators=[MinValueValidator(0.0)])
    num_completions = models.FloatField(null=True, blank=True, validators=[MinValueValidator(0.0)])
    status_playing = models.BooleanField(default=False)
    status_completed = models.BooleanField(default=False)
    status_retired = models.BooleanField(default=False)

    objects = UserGameLibraryManager()

    def clean(self):
        if self.rating is not None and not (1.0 <= self.rating <= 10.0):
            raise ValidationError("Rating must be between 1.0 and 10.0")
        if self.hours_played is not None and not (0.0 <= self.hours_played):
            raise ValidationError("Minimum hours played must be above or equal 0.0")
        if self.num_completions is not None and not (0 <= self.num_completions):
            raise ValidationError("Number of completions must be above or equal 0")

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.username}'s game library entry - {self.game.name}"

    class Meta:
        unique_together = ("user", "game")
