import sys
import os
import pkg_resources
import unittest

from balda.settings import BASE_DIR


class TestEnv(unittest.TestCase):

    def test_in_virtualenv(self):
        self.assertNotEqual(sys.prefix, sys.base_prefix)

    def test_requirements_installed(self):
        with open(os.path.join(BASE_DIR, 'requirements.txt')) as inf:
            dependencies = list(map(lambda x: x.strip('\n'), inf.readlines()))

        pkg_resources.require(dependencies)


if __name__ == '__main__':
    unittest.main()
