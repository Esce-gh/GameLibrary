from unittest.mock import patch

from django.contrib.auth.models import User
from django.http import Http404
from django.test import TestCase
from django.urls import reverse
from GameLibrary import settings
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
    def test_should_show_a_message_when_query_length_less_than_4(self):
        response = self.client.get(reverse("main:search"), {'query': ' 12 '})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Please enter at least 3 characters.')

    def test_should_not_show_a_message_when_query_length_correct(self):
        response = self.client.get(reverse("main:search"), {'query': ' 123 '})
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Please enter at least 3 characters.')


class GameViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='test', password='test', pk=1)
        self.client.login(username='test', password='test')
        self.game = Game(name="mock_game", id=1)
        self.game.save()

    def test_should_show_game_when_found(self):
        response = self.client.get(reverse("main:game", args=[self.game.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'mock_game')

    @patch('main.views.get_object_or_404')
    def test_should_not_show_game_when_not_found(self, mock_get_object):
        mock_get_object.side_effect = Http404
        response = self.client.get(reverse("main:game", args=[1]))
        self.assertEqual(response.status_code, 404)

    def test_should_show_user_input_when_authenticated_and_library_entry_found(self):
        library_entry = UserGameLibrary(user_id=self.user.id, game_id=self.game.id, review='mock_review', rating=5.5)
        library_entry.save()

        response = self.client.get(reverse("main:game", args=[self.game.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'mock_review')
        self.assertContains(response, '5.5')
        self.assertContains(response, 'Remove game from library')
        self.assertNotContains(response, 'Add game to library')

    def test_should_not_show_user_input_when_authenticated_and_library_entry_not_found(self):
        response = self.client.get(reverse("main:game", args=[self.game.id]))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'mock_review')
        self.assertNotContains(response, '5.5')
        self.assertNotContains(response, 'Remove game from library')
        self.assertContains(response, 'Add game to library')

    def test_should_not_show_user_input_when_not_authenticated(self):
        self.client.logout()
        response = self.client.get(reverse("main:game", args=[self.game.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'mock_game')
        self.assertNotContains(response, "<label for='review'>")
        self.assertNotContains(response, "<label for='rating'>")
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
        response = self.client.post(reverse("main:game_edit", args=[self.game.id]))
        self.assertRedirects(response, reverse("login"))

    def test_should_redirect_when_game_delete_not_authorized(self):
        self.client.logout()
        response = self.client.post(reverse("main:game_delete", args=[self.game.id]))
        self.assertRedirects(response, reverse("login"))
