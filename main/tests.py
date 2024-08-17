from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse
from GameLibrary import settings
from main.models import Game


# Create your tests here.
class GameManagerTests(TestCase):
    def test_search(self):
        game1 = Game(name='doom', igdb_id=1)
        game2 = Game(name='_doom_', igdb_id=2)
        game3 = Game(name='quake', igdb_id=3)
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
        game1 = Game(name='_doom_', igdb_id=1)
        game2 = Game(name='quake', igdb_id=2)
        Game.games.bulk_create([
            game1,
            game2,
        ])
        response = self.client.get(reverse("main:search"), {'query': 'doom'})
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'quake')
        self.assertContains(response, '_doom_')

    def test_should_show_find_more_button_on_last_page(self):
        Game.games.create(name='doom', igdb_id=1)
        response = self.client.get(reverse("main:search"), {'query': 'doom'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'find more')

    def test_should_not_show_find_more_button_when_not_on_last_page(self):
        for i in range(settings.GLOBAL_SETTINGS['MAX_GAMES_PER_PAGE'] + 1):
            Game.games.create(name=f'game {i}', igdb_id=i)
        response = self.client.get(reverse("main:search"), {'query': 'game'})
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'find more')

    @patch('main.models.GameManager.search_api_excluding')
    def test_should_show_api_games_when_found(self, mock_api_search):
        mock_api_search.return_value = [{'name': 'epic_name', 'igdb_id': 1}]

        response = self.client.get(reverse("main:search"), {'query': 'game', 'api_search': '1'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'epic_name')

    @patch('main.models.GameManager.search_api_excluding')
    def test_should_show_error_when_api_games_not_found(self, mock_api_search):
        mock_api_search.return_value = []

        response = self.client.get(reverse("main:search"), {'query': 'game', 'api_search': '1'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Couldn't find more results")
