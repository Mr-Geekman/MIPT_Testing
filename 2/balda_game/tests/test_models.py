import time
from datetime import datetime

import unittest
from django.test import TestCase, override_settings
from django.contrib.auth.models import User
from django.core.cache import cache

from balda_game.models import UserPlayer, GameModel
from balda_game.lib.db.Move import Move
from balda_game.lib.field.Letter import CellLetter
from balda_game.lib.JSONlib import serialize_game_log_to_json, deserialize_game_log_from_json


class TestUserPlayer(TestCase):

    def setUp(self):
        user = User.objects.create_user(
            username='test',
            email='test@test.com',
            password='123'
        )
        self.user_player = UserPlayer.objects.create(
            user=user,
            wins=0, draws=0, loses=0, rating=1500, was_online=datetime.now()
        )

    def test_str(self):
        player = UserPlayer.objects.get(id=self.user_player.id)
        player_str_got = str(player)
        player_str_expected = f'test Wins: 0 Draws: 0 Loses: 0 Rating: 1500'
        self.assertEqual(player_str_got, player_str_expected)

    def test_last_seen(self):
        moment = datetime.now()
        key = f'seen_{self.user_player.user.username}'
        cache.set(key, moment, 10)
        result = self.user_player.last_seen()
        self.assertEqual(result, moment)

    def test_last_seen_in_game(self):
        moment = datetime.now()
        game_id = 1
        key = f'seen_{game_id}_{self.user_player.user.username}'
        cache.set(key, moment, 10)
        result = self.user_player.last_seen_in_game(game_id)
        self.assertEqual(result, moment)

    def test_last_waited(self):
        moment = datetime.now()
        key = f'wait_{self.user_player.user.username}'
        cache.set(key, moment, 10)
        result = self.user_player.last_waited()
        self.assertEqual(result, moment)

    @override_settings(USER_ONLINE_TIMEOUT=60)
    def test_online_true(self):
        moment = datetime.now()
        key = f'seen_{self.user_player.user.username}'
        cache.set(key, moment, 10)
        result = self.user_player.online()
        self.assertTrue(result)

    def test_online_false_none(self):
        key = f'seen_{self.user_player.user.username}'
        cache.delete(key)
        result = self.user_player.online()
        self.assertFalse(result)

    @override_settings(USER_ONLINE_TIMEOUT=1)
    def test_online_false_timeout(self):
        moment = datetime.now()
        key = f'seen_{self.user_player.user.username}'
        cache.set(key, moment, 10)
        time.sleep(1)
        result = self.user_player.online()
        self.assertFalse(result)

    @override_settings(USER_ONLINE_GAME_TIMEOUT=60)
    def test_online_in_game_seen_ok_waited_ok(self):
        moment = datetime.now()

        game_id = 1
        key = f'seen_{game_id}_{self.user_player.user.username}'
        cache.set(key, moment, 10)

        key_wait = f'wait_{self.user_player.user.username}'
        cache.set(key_wait, moment, 10)

        result = self.user_player.online_in_game(game_id)
        self.assertTrue(result)

    @override_settings(USER_ONLINE_GAME_TIMEOUT=60)
    def test_online_in_game_seen_ok_waited_expired(self):
        moment = datetime.now()

        game_id = 1
        key = f'seen_{game_id}_{self.user_player.user.username}'
        cache.set(key, moment, 10)

        key_wait = f'wait_{self.user_player.user.username}'
        cache.set(key_wait, moment, 1)

        time.sleep(1)
        result = self.user_player.online_in_game(game_id)
        self.assertTrue(result)

    @override_settings(USER_ONLINE_GAME_TIMEOUT=60)
    def test_online_in_game_seen_ok_waited_none(self):
        moment = datetime.now()

        game_id = 1
        key = f'seen_{game_id}_{self.user_player.user.username}'
        cache.set(key, moment, 10)

        key_wait = f'wait_{self.user_player.user.username}'
        cache.delete(key_wait)

        result = self.user_player.online_in_game(game_id)
        self.assertTrue(result)

    def test_online_in_game_seen_expired_waited_ok(self):
        moment = datetime.now()

        game_id = 1
        key = f'seen_{game_id}_{self.user_player.user.username}'
        cache.set(key, moment, 1)

        key_wait = f'wait_{self.user_player.user.username}'
        cache.set(key_wait, moment, 10)

        time.sleep(1)
        result = self.user_player.online_in_game(game_id)
        self.assertTrue(result)

    def test_online_in_game_seen_expired_waited_expired(self):
        moment = datetime.now()

        game_id = 1
        key = f'seen_{game_id}_{self.user_player.user.username}'
        cache.set(key, moment, 1)

        key_wait = f'wait_{self.user_player.user.username}'
        cache.set(key_wait, moment, 1)

        time.sleep(1)
        result = self.user_player.online_in_game(game_id)
        self.assertFalse(result)

    def test_online_in_game_seen_expired_waited_none(self):
        moment = datetime.now()

        game_id = 1
        key = f'seen_{game_id}_{self.user_player.user.username}'
        cache.set(key, moment, 1)

        key_wait = f'wait_{self.user_player.user.username}'
        cache.delete(key_wait)

        time.sleep(1)
        result = self.user_player.online_in_game(game_id)
        self.assertFalse(result)

    def test_online_in_game_seen_none_waited_ok(self):
        moment = datetime.now()

        game_id = 1
        key = f'seen_{game_id}_{self.user_player.user.username}'
        cache.delete(key)

        key_wait = f'wait_{self.user_player.user.username}'
        cache.set(key_wait, moment, 10)

        result = self.user_player.online_in_game(game_id)
        self.assertTrue(result)

    def test_online_in_game_seen_none_waited_expired(self):
        moment = datetime.now()

        game_id = 1
        key = f'seen_{game_id}_{self.user_player.user.username}'
        cache.delete(key)

        key_wait = f'wait_{self.user_player.user.username}'
        cache.set(key_wait, moment, 1)

        time.sleep(1)
        result = self.user_player.online_in_game(game_id)
        self.assertFalse(result)

    def test_online_in_game_seen_none_waited_none(self):
        game_id = 1
        key = f'seen_{game_id}_{self.user_player.user.username}'
        cache.delete(key)

        key_wait = f'wait_{self.user_player.user.username}'
        cache.delete(key_wait)

        time.sleep(1)
        result = self.user_player.online_in_game(game_id)
        self.assertFalse(result)


class TestGameModel(TestCase):

    def setUp(self):
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
        self.game = GameModel.objects.create(
            first_user=user_1, second_user=user_2, field_size=5
        )

        move = Move()
        move.set_added_letter(CellLetter(0, 0, 'B'))
        move.set_word_structure([CellLetter(0, 0, 'B'),
                                 CellLetter(0, 1, 'A')])
        self.list_moves = [move, move]

    def test_str(self):
        game = GameModel.objects.get(id=self.game.id)
        game_str_got = str(game)
        game_str_expected = str(self.game.id)
        self.assertEqual(game_str_got, game_str_expected)

    def test_set_game_log(self):
        expected = serialize_game_log_to_json(self.list_moves)
        self.game.set_game_log(self.list_moves)
        self.assertEqual(expected, self.game.game_log)

    def test_set_first_word(self):
        expected = 'word'
        self.game.set_first_word(expected)
        self.assertEqual(expected, self.game.first_word)

    def test_get_game_log(self):
        expected = serialize_game_log_to_json(self.list_moves)
        self.game.set_game_log(self.list_moves)
        result = serialize_game_log_to_json(self.game.get_game_log())
        self.assertEqual(expected, result)


if __name__ == '__main__':
    unittest.main()
