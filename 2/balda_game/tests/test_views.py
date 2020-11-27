import json
from datetime import datetime

from django.test import TestCase, override_settings
import unittest
from django.contrib.auth.models import User
from django.urls import reverse
from django.core.cache import cache
from http import HTTPStatus

from balda_game.models import UserPlayer, GameModel
from balda_game.lib.GameProcessor import GameProcessor
from balda_game.forms.CreationUserForm import CreationUserForm


def fill_test_db():
    bot_easy = User.objects.create_user(
        username='EASYBOT',
        email='easybot@test.com',
        password='123'
    )
    user_1 = User.objects.create_user(
        username='test-1',
        email='test-1@test.com',
        password='123'
    )
    user_2 = User.objects.create_user(
        username='test-2',
        email='test-2@test.com',
        password='123'
    )
    bot_easy.save()
    user_1.save()
    user_2.save()

    bot_easy_player = UserPlayer.objects.create(
        user=bot_easy,
        wins=0, draws=0, loses=0, rating=1500, was_online=datetime.now()
    )
    user_player_1 = UserPlayer.objects.create(
        user=user_1,
        wins=0, draws=0, loses=0, rating=1500, was_online=datetime.now()
    )
    user_player_2 = UserPlayer.objects.create(
        user=user_2,
        wins=0, draws=0, loses=0, rating=1500, was_online=datetime.now()
    )
    bot_easy_player.save()
    user_player_1.save()
    user_player_2.save()

    return user_player_1, user_player_2, bot_easy


class TestIndex(TestCase):

    def test_view_uses_correct_template(self):
        response = self.client.get(reverse('index'))
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response, 'index.html')


class TestRegistration(TestCase):

    def test_get(self):
        response = self.client.get(reverse('register'))
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response, 'register.html')
        self.assertIsInstance(response.context['form'], CreationUserForm)

    def test_post_invalid(self):
        response = self.client.post(
            reverse('register'), data={
                'password1': '123'
            }
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response, 'register.html')
        self.assertIsInstance(response.context['form'], CreationUserForm)

    def test_post_valid(self):
        response = self.client.post(
            reverse('register'), data={
                'first_name': 'Test',
                'second_name': 'Test',
                'username': 'test',
                'password1': '123',
                'password2': '123'
            }
        )
        self.assertRedirects(response, '/')
        try:
            User.objects.get(username='test')
        except User.DoesNotExist:
            self.assertTrue(False)


class TestLogin(TestCase):

    def setUp(self):
        user_player_1, _, _ = fill_test_db()
        self.user_player_1 = user_player_1

    def test_get(self):
        response = self.client.get(reverse('login_view'))
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response, 'login.html')

    def test_user_none(self):
        response = self.client.post(
            reverse('login_view'),
            data={
                'username': 'not_existent',
                'password': 'not_existent'
            }
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response, 'login.html')
        self.assertEqual(response.context['message'],
                         'Wrong username or password')

    def test_user_not_active(self):
        """No need:
        https://stackoverflow.com/questions/43184151/django-user-is-active"""
        pass

    def test_success(self):
        start_moment = datetime.now()
        response = self.client.post(
            reverse('login_view'),
            data={
                'username': self.user_player_1.user.username,
                'password': '123'
            }, follow=True
        )
        self.assertRedirects(response, '/')
        # проверим, что пользователь залогинился
        self.assertTrue(self.user_player_1.user.is_active)

        # проверим, что статус пользователя изменился
        last_online = self.user_player_1.last_seen()
        self.assertGreaterEqual(last_online, start_moment)


class TestGameWait(TestCase):

    def setUp(self):
        user_player_1, _, _ = fill_test_db()
        self.user_player_1 = user_player_1

    def test_not_logged_in(self):
        response = self.client.get(reverse('game_wait'))
        self.assertRedirects(response, '/login/?next=/game_wait/')

    def test_success(self):
        start_moment = datetime.now()
        self.client.login(username=self.user_player_1.user.username,
                          password='123')
        response = self.client.get(reverse('game_wait'))
        self.assertTrue(
            self.user_player_1.user in GameProcessor.list_waiting_players
        )
        self.assertTemplateUsed(response, 'game_wait.html')
        cache_value = cache.get(f'wait_{self.user_player_1.user.username}')
        self.assertTrue(cache_value is not None)

        # проверим, что статус пользователя обновился
        last_waited = self.user_player_1.last_waited()
        self.assertGreaterEqual(last_waited, start_moment)


class TestWaitQuery(TestCase):

    def setUp(self):
        user_player_1, user_player_2, _ = fill_test_db()
        self.user_player_1 = user_player_1
        self.user_player_2 = user_player_2

    def test_not_logged_in(self):
        response = self.client.get(reverse('wait_query'))
        self.assertRedirects(response, '/login/?next=/wait_query/')

    @override_settings(USER_LAST_SEEN_TIMEOUT=60)
    def test_value_can_start_game(self):
        start_moment = datetime.now()
        # оба пользователя записываются на игру
        self.client.login(username=self.user_player_2.user.username,
                          password='123')
        self.client.get(reverse('game_wait'))
        self.client.login(username=self.user_player_1.user.username,
                          password='123')
        self.client.get(reverse('game_wait'))
        # второй пользователь проверяет, что игра началась
        response = self.client.get(reverse('wait_query'))
        self.assertEqual(response.status_code, HTTPStatus.OK)
        response_str = response.content.decode('utf-8')
        try:
            response_json = json.loads(response_str)
            game_id = response_json['game']
            self.assertGreaterEqual(game_id, 1)

            # проверим, что статус пользователя обновился
            last_seen_in_game = self.user_player_1.last_seen_in_game(game_id)
            self.assertGreaterEqual(last_seen_in_game, start_moment)
        except json.JSONDecodeError:
            self.assertTrue(False)

    @override_settings(USER_LAST_SEEN_TIMEOUT=60)
    def test_value_cannot_start_game(self):
        start_moment = datetime.now()
        # один пользователь записывается на игру
        self.client.login(username=self.user_player_1.user.username,
                          password='123')
        self.client.get(reverse('wait_query'))
        # пользователь проверяет, что игра не может начаться
        response = self.client.get(reverse('wait_query'))
        self.assertEqual(response.status_code, HTTPStatus.OK)
        response_str = response.content.decode('utf-8')
        try:
            response_json = json.loads(response_str)
            game_id = response_json['game']
            self.assertEqual(game_id, -1)
            # проверим, что статус пользователя не обновился
            last_seen_in_game = self.user_player_1.last_seen_in_game(game_id)
            self.assertTrue(
                last_seen_in_game is None or last_seen_in_game <= start_moment
            )
        except json.JSONDecodeError:
            self.assertTrue(False)


class TestPlayWithBot(TestCase):

    def setUp(self):
        user_player_1, _, _ = fill_test_db()
        self.user_player_1 = user_player_1

    def test_not_logged_in(self):
        response = self.client.get(reverse('play_with_bot'))
        self.assertRedirects(response, '/login/?next=/play_with_bot/')

    def test_success(self):
        self.client.login(username=self.user_player_1.user.username,
                          password='123')
        response = self.client.get(reverse('play_with_bot'))
        self.assertEqual(response.status_code, HTTPStatus.OK)
        response_str = response.content.decode('utf-8')
        try:
            response_json = json.loads(response_str)
            game_id = response_json['game']
            self.assertGreaterEqual(game_id, 1)
        except json.JSONDecodeError:
            self.assertTrue(False)


class TestStartGame(TestCase):

    def setUp(self):
        user_player_1, user_player_2, bot_easy = fill_test_db()
        self.user_player_1 = user_player_1
        self.user_player_2 = user_player_2
        self.bot_easy = bot_easy

    def test_not_exists(self):
        response = self.client.get(
            reverse('start_game', kwargs={'game_id': str(1)})
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response, 'not_started_game.html')

    def test_game_ended(self):
        game = GameModel.objects.create(
            first_user=self.user_player_1.user,
            second_user=self.user_player_2.user,
            field_size=5,
            status='end'
        )
        game.save()
        response = self.client.get(
            reverse('start_game', kwargs={'game_id': str(game.id)})
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response, 'ended_game.html')

    def test_started(self):
        # оба пользователя записываются на игру
        self.client.login(username=self.user_player_1.user.username,
                          password='123')
        self.client.get(reverse('game_wait'))
        self.client.login(username=self.user_player_2.user.username,
                          password='123')
        # один из пользователей стартует игру
        self.client.get(reverse('game_wait'))
        response = self.client.get(reverse('wait_query'))
        response_str = response.content.decode('utf-8')
        try:
            # получаем номер игры
            response_json = json.loads(response_str)
            game_id = response_json['game']
            self.assertGreaterEqual(game_id, 1)

            response = self.client.get(
                reverse('start_game', kwargs={'game_id': str(game_id)})
            )
            self.assertEqual(response.status_code, HTTPStatus.OK)
            self.assertTemplateUsed(response, 'field.html')

            # завершаем игру, чтобы при удалении БД не было проблем
            self.client.get(
                reverse('give_up', kwargs={'game_id': str(game_id)})
            )
        except json.JSONDecodeError:
            self.assertTrue(False)


if __name__ == '__main__':
    unittest.main()
