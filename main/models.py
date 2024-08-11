from django.contrib.auth.models import User
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


# Create your models here.
class Game(models.Model):
    name = models.CharField(max_length=100)

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
