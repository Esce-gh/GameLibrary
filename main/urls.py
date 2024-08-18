from django.urls import path
from . import views


app_name = 'main'
urlpatterns = [
    path("", views.index, name="index"),
    path("search", views.search, name="search"),
    path("library/", views.library, name="library"),
    path("game/<int:game_id>/", views.game, name="game"),
    path("game/<int:game_id>/add", views.game_add, name="game_add"),
    path("game/<int:game_id>/edit", views.game_update, name="game_edit"),
    path("game/<int:game_id>/delete", views.game_delete, name="game_delete"),
]
