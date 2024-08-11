from django.contrib import admin

from main.models import Game, UserGameLibrary

# Register your models here.
admin.site.register(Game)
admin.site.register(UserGameLibrary)
