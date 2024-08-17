from unittest import mock

from django.db import IntegrityError
from django.test import TestCase
from django.urls import reverse

from GameLibrary import settings
from main.models import Game, GameManager


# Create your tests here.
class GameManagerTests(TestCase):
    def test_search(self):
        game1 = Game(name='doom', igdb_id=0)
        game2 = Game(name='_doom_', igdb_id=1)
        game3 = Game(name='quake', igdb_id=2)
        Game.games.bulk_create([
            game1,
            game2,
            game3,
        ])
        result = Game.games.search('doom')
        self.assertTrue(game1 in result)
        self.assertTrue(game2 in result)
        self.assertTrue(game3 not in result)


class SearchViewTests(TestCase):
    def test_should_show_a_message_when_query_length_less_than_4(self):
        response = self.client.get(reverse("main:search"), {'query': ' 123 '})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Please enter at least 4 characters.')

    def test_should_not_show_a_message_when_query_length_correct(self):
        response = self.client.get(reverse("main:search"), {'query': ' 1234 '})
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Please enter at least 4 characters.')

    def test_search(self):
        game2 = Game(name='_doom_', igdb_id=1)
        game3 = Game(name='quake', igdb_id=2)
        Game.games.bulk_create([
            game2,
            game3,
        ])
        response = self.client.get(reverse("main:search"), {'query': 'doom'})
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'quake')
        self.assertContains(response, '_doom_')

    def test_find_more_button_on_last_page(self):
        Game.games.create(name='doom', igdb_id=0)
        response = self.client.get(reverse("main:search"), {'query': 'doom'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'find more')

    def test_find_more_button_disabled(self):
        for i in range(settings.GLOBAL_SETTINGS['MAX_GAMES_PER_PAGE'] + 1):
            Game.games.create(name=f'game {i}', igdb_id=i)
        response = self.client.get(reverse("main:search"), {'query': 'game'})
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'find more')
