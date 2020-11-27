from django.test import TestCase
import unittest
from django.contrib.auth.models import User

from balda_game.models import UserPlayer
from balda_game.forms.CreationUserForm import CreationUserForm


class TestCreationUserForm(TestCase):

    def test_init_ok(self):
        form = CreationUserForm(data={
            'first_name': 'Test',
            'last_name': 'Test',
            'username': 'new_test',
            'password1': '123',
            'password2': '123'
        })
        self.assertTrue(form.is_valid())

    def test_save_no_commit(self):
        form = CreationUserForm(data={
            'first_name': 'Test',
            'last_name': 'Test',
            'username': 'new_test',
            'password1': '123',
            'password2': '123'
        })
        form.save(commit=False)
        try:
            user = User.objects.get(username='new_test')
            with self.assertRaises(UserPlayer.DoesNotExist):
                UserPlayer.objects.get(user=user)
        except User.DoesNotExist:
            self.assertTrue(False)

    def test_save_commit(self):
        form = CreationUserForm(data={
            'first_name': 'Test',
            'last_name': 'Test',
            'username': 'new_test',
            'password1': '123',
            'password2': '123'
        })
        form.save(commit=True)
        try:
            user = User.objects.get(username='new_test')
            UserPlayer.objects.get(user=user)
        except (User.DoesNotExist, UserPlayer.DoesNotExist):
            self.assertTrue(False)


if __name__ == '__main__':
    unittest.main()
