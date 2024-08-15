from django.contrib.auth.models import User
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models, IntegrityError
import logging
from .services import Igdb


logger = logging.getLogger(__name__)


class GameManager(models.Manager):
    def search(self, query):
        return super().get_queryset().filter(name__icontains=query)

    def search_api_excluding(self, query, found_games):
        igdb_api = Igdb()
        excluded_ids = [game.igdb_id for game in found_games]
        games_api = igdb_api.extended_search(query, excluded_ids)
        self.save_games(games_api)
        return games_api

    def save_games(self, games):
        try:
            super().bulk_create([Game(name=game["name"], igdb_id=game["id"]) for game in games])
        except IntegrityError:
            logger.exception("Failed to save, game already exists in database")

    def get_queryset(self):
        return super().get_queryset().all()


# Create your models here.
class Game(models.Model):
    name = models.CharField(max_length=100)
    igdb_id = models.IntegerField(unique=True)
    games = GameManager()

    def __str__(self):
        return self.name


class UserGameLibrary(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    review = models.TextField()
    rating = models.FloatField(validators=[MinValueValidator(0.0), MaxValueValidator(10.0)])

    def __str__(self):
        return f"{self.user.username}'s game library entry - {self.game.name}"

    class Meta:
        unique_together = ("user", "game")
