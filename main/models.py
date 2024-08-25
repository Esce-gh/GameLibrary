from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models, IntegrityError
import logging
from .services import Igdb


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

    def _save_games_from_json(self, games):
        for game in games:
            try:
                self.create(name=game["name"], id=game["id"])
            except IntegrityError:
                logger.exception(f"Failed to save, game with {game['id']} ID already exists in database")

    def get_queryset(self):
        return super().get_queryset()


class Game(models.Model):
    name = models.CharField(max_length=100)
    id = models.IntegerField(unique=True, primary_key=True)
    games = GameManager()

    def __str__(self):
        return self.name


class UserGameLibraryManager(models.Manager):
    def get_library_entry(self, user_id, game_id):
        return self.filter(user_id=user_id, game_id=game_id).first()
    
    def get_user_library(self, user_id):
        return self.filter(user_id=user_id)

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

    def update_library(self, user_id, game_id, review, rating):
        try:
            entry = self.get(user_id=user_id, game_id=game_id)
            entry.review = review
            if rating == "":
                entry.rating = None
            else:
                entry.rating = float(rating)
            entry.save()
            return True
        except ValidationError:
            logger.exception(f"Validation error for user {user_id}, game {game_id}")
            return False
        except UserGameLibrary.DoesNotExist:
            logger.exception(f"Cannot update an entry that doesn't exist. Game {game_id}, user {user_id}")

    def delete_library(self, user_id, game_id):
        try:
            self.filter(user_id=user_id, game_id=game_id).delete()
        except IntegrityError:
            logger.exception(f"Failed to delete user {user_id}, game {game_id}")

    def get_queryset(self):
        return super().get_queryset()


class UserGameLibrary(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    review = models.TextField(null=True, blank=True)    # TODO: char limit
    rating = models.FloatField(validators=[MinValueValidator(1.0), MaxValueValidator(10.0)], null=True, blank=True)
    objects = UserGameLibraryManager()

    def clean(self):
        if self.rating is not None and not (1.0 <= self.rating <= 10.0):
            raise ValidationError("Rating must be between 1.0 and 10.0")

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.username}'s game library entry - {self.game.name}"

    class Meta:
        unique_together = ("user", "game")
