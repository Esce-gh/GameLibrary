from django.urls import path
from . import views

app_name = 'main'
urlpatterns = [
    path("", views.index, name="index"),
    path("settings", views.user_settings, name="settings"),
    path("search", views.search, name="search"),
    path("search/ajax", views.ajax_search, name="ajax_search"),
    path("library/", views.library, name="library"),
    path("library/search", views.library_search, name="library_search"),
    path("library/import", views.library_import, name="library_import"),
    path("game/<int:game_id>/", views.game, name="game"),
    path("game/<int:game_id>/add", views.game_add, name="game_add"),
    path("game/<int:game_id>/edit", views.game_edit, name="game_edit"),
    path("game/<int:game_id>/delete", views.game_delete, name="game_delete"),
    path("fetch-cover-small/<str:cover_id>", views.fetch_cover_small, name="fetch_cover_small"),
]
