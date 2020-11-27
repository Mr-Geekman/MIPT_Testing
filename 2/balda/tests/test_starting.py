import os
import unittest
import subprocess
import time

from balda.settings import BASE_DIR


class TestStarting(unittest.TestCase):

    def test_migrations(self):
        # общие миграции
        completed_process = subprocess.run(
            f"python {os.path.join(BASE_DIR, 'manage.py')} makemigrations",
            shell=True
        )
        self.assertEqual(completed_process.returncode, 0)

        completed_process = subprocess.run(
            f"python {os.path.join(BASE_DIR, 'manage.py')} migrate",
            shell=True
        )
        self.assertEqual(completed_process.returncode, 0)

        # миграции приложения
        completed_process = subprocess.run(
            f"python {os.path.join(BASE_DIR, 'manage.py')} makemigrations balda_game",
            shell=True
        )
        self.assertEqual(completed_process.returncode, 0)

        completed_process = subprocess.run(
            f"python {os.path.join(BASE_DIR, 'manage.py')} migrate balda_game",
            shell=True
        )
        self.assertEqual(completed_process.returncode, 0)

    def test_server(self):
        try:
            process = subprocess.Popen(
                f"python {os.path.join(BASE_DIR, 'manage.py')} runserver",
                shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            time.sleep(3)
            process.terminate()
            output, err = process.communicate()
            err = err.decode('utf-8')
            # Как минимум одна строка и одна пустая строка там будут всегда.
            self.assertLessEqual(len(err.split('\n')), 2)

        except subprocess.CalledProcessError:
            self.assertTrue(False)


if __name__ == '__main__':
    unittest.main()
