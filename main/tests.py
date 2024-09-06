from unittest.mock import patch

from django.contrib.auth.models import User
from django.http import Http404
from django.test import TestCase
from django.urls import reverse
from main.models import Game, UserGameLibrary


# Create your tests here.
class GameManagerTests(TestCase):
    def test_search(self):
        game1 = Game(name='doom', id=1)
        game2 = Game(name='_doom_', id=2)
        game3 = Game(name='quake', id=3)
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
    def setUp(self):
        self.user = User.objects.create_user(username='test', password='test', pk=1)
        self.client.login(username='test', password='test')
        self.game = Game(name="doom", id=1)
        self.game.save()

    def test_should_show_a_message_when_query_length_less_than_3(self):
        response = self.client.get(reverse("main:search"), {'query': ' 12 '})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Please enter at least 3 characters.')

    def test_should_not_show_a_message_when_query_length_correct(self):
        response = self.client.get(reverse("main:search"), {'query': ' 123 '})
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Please enter at least 3 characters.')

    def test_should_return_403_when_query_length_less_than_3(self):
        response = self.client.get(reverse("main:ajax_search"), {'query': ' 12 '})
        self.assertEqual(response.status_code, 403)

    def test_should_not_return_403_when_query_length_correct(self):
        response = self.client.get(reverse("main:ajax_search"), {'query': ' 123 '})
        self.assertNotEqual(response.status_code, 403)

    @patch('main.views.cache.get')
    def test_should_return_cached_values_when_found(self, cache_get):
        cache_get.return_value = {'test': 'test_game'}
        response = self.client.get(reverse("main:ajax_search"), {'query': 'doom'})
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {'test': 'test_game'})

    @patch('main.views.cache.get')
    def test_should_not_return_cached_values_when_not_found(self, cache_get):
        cache_get.return_value = None
        response = self.client.get(reverse("main:ajax_search"), {'query': 'doom'})
        self.assertEqual(response.status_code, 200)
        self.assertJSONNotEqual(response.content, {'test': 'test_game'})

    def test_should_return_db_game_when_found(self):
        response = self.client.get(reverse("main:ajax_search"), {'query': 'doom'})
        self.assertEqual(response.status_code, 200)
        json = response.content.decode('utf-8')
        self.assertIn("doom", json)
        self.assertIn("\"has_next\": true", json)

    @patch('main.views.Game.games.search_api_excluding')
    def test_should_not_return_db_game_when_not_found(self, api_mock):
        api_mock.return_value = {}
        response = self.client.get(reverse("main:ajax_search"), {'query': 'some_game_that_does_not_exist'})
        self.assertEqual(response.status_code, 200)
        self.assertJSONNotEqual(response.content, {'test': 'some_game_that_does_not_exist'})
        self.assertJSONEqual(response.content, {'items': [], 'has_next': False})

    @patch('main.models.UserGameLibrary.objects.advanced_search')
    def test_library_search(self, mock_search):
        mock_search.return_value = UserGameLibrary.objects.none()
        query_params = {
            'query': 'test',
            'sort': 'game__name',
            'order': 1,
            'min_rating': 7,
            'min_hours': 10,
            'status': 'completed',
            'page': 1
        }
        response = self.client.get(reverse("main:library_search"), query_params)
        mock_search.assert_called_once_with(self.user.id, 'test', 'game__name', 1, '7', '10', 'completed')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        response_data = response.json()
        self.assertIn('items', response_data)
        self.assertIn('num_pages', response_data)
        self.assertIsInstance(response_data['items'], list)
        self.assertIsInstance(response_data['num_pages'], int)



class GameViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='test', password='test', pk=1)
        self.client.login(username='test', password='test')
        self.game = Game(name="test_game", id=1)
        self.game.save()

    def test_should_show_game_when_found(self):
        response = self.client.get(reverse("main:game", args=[self.game.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'test_game')

    @patch('main.views.get_object_or_404')
    def test_should_not_show_game_when_not_found(self, mock_get_object):
        mock_get_object.side_effect = Http404
        response = self.client.get(reverse("main:game", args=[1]))
        self.assertEqual(response.status_code, 404)

    def test_should_show_user_input_when_authenticated_and_library_entry_found(self):
        library_entry = UserGameLibrary(user_id=self.user.id, game_id=self.game.id, review='test_review', rating=5.5,
                                        hours_played=10, num_completions=6.5)
        library_entry.save()

        response = self.client.get(reverse("main:game", args=[self.game.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'test_review')
        self.assertContains(response, '5.5')
        self.assertContains(response, '10.0')
        self.assertContains(response, '6.5')
        self.assertContains(response, 'Remove game from library')
        self.assertNotContains(response, 'Add game to library')

    def test_should_not_show_user_input_when_authenticated_and_library_entry_not_found(self):
        response = self.client.get(reverse("main:game", args=[self.game.id]))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Remove game from library')
        self.assertContains(response, 'Add game to library')

    def test_should_not_show_user_input_when_not_authenticated(self):
        self.client.logout()
        response = self.client.get(reverse("main:game", args=[self.game.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'test_game')
        self.assertNotContains(response, "<form id=\"library-entry-form\">")
        self.assertNotContains(response, "Add game to library")
        self.assertNotContains(response, 'Remove game from library')

    def test_should_return_405_when_game_add_method_not_post(self):
        response = self.client.get(reverse("main:game_add", args=[self.game.id]))
        self.assertEqual(response.status_code, 405)

    def test_should_return_405_when_game_update_method_not_post(self):
        response = self.client.get(reverse("main:game_edit", args=[self.game.id]))
        self.assertEqual(response.status_code, 405)

    def test_should_return_405_when_game_delete_method_not_post(self):
        response = self.client.get(reverse("main:game_delete", args=[self.game.id]))
        self.assertEqual(response.status_code, 405)

    def test_should_redirect_when_game_add_not_authorized(self):
        self.client.logout()
        response = self.client.post(reverse("main:game_add", args=[self.game.id]))
        self.assertRedirects(response, reverse("login"))

    def test_should_redirect_when_game_edit_not_authorized(self):
        self.client.logout()
        response = self.client.put(reverse("main:game_edit", args=[self.game.id]))
        self.assertRedirects(response, reverse("login"))

    def test_should_redirect_when_game_delete_not_authorized(self):
        self.client.logout()
        response = self.client.post(reverse("main:game_delete", args=[self.game.id]))
        self.assertRedirects(response, reverse("login"))
