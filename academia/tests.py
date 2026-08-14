from types import SimpleNamespace

from django.test import SimpleTestCase

from .views import AcademyAdminRequiredMixin


class AcademyAccessTests(SimpleTestCase):
    def test_only_superuser_can_access_academy_screens(self):
        view = AcademyAdminRequiredMixin()
        view.request = SimpleNamespace(
            user=SimpleNamespace(is_superuser=True),
        )
        self.assertTrue(view.test_func())

        view.request.user.is_superuser = False
        self.assertFalse(view.test_func())
