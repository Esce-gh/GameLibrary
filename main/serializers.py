from rest_framework import serializers
from main.models import UserGameLibrary, Game


class GameSerializer(serializers.ModelSerializer):
    class Meta:
        model = Game
        fields = '__all__'


class UserGameLibrarySerializer(serializers.ModelSerializer):
    game = GameSerializer()

    class Meta:
        model = UserGameLibrary
        fields = '__all__'
