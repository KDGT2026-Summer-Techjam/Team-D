from django.test import TestCase

from accounts.forms import AccountDeletionForm, RegistrationForm
from accounts.models import User


class RegistrationFormTests(TestCase):
    def test_valid_registration_form(self):
        form = RegistrationForm(
            data={
                "email": "user@example.com",
                "name": "参加者",
                "role": User.Role.PARTICIPANT,
                "password1": "SafePassword123!",
                "password2": "SafePassword123!",
            }
        )

        self.assertTrue(form.is_valid(), form.errors)

    def test_duplicate_email_is_rejected(self):
        User.objects.create_user(
            email="used@example.com",
            password="SafePassword123!",
            name="登録済み",
        )
        form = RegistrationForm(
            data={
                "email": "used@example.com",
                "name": "別ユーザー",
                "role": User.Role.PARTICIPANT,
                "password1": "SafePassword123!",
                "password2": "SafePassword123!",
            }
        )

        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)

    def test_duplicate_email_is_rejected_regardless_of_case(self):
        User.objects.create_user(
            email="case@example.com",
            password="SafePassword123!",
            name="登録済み",
        )
        form = RegistrationForm(
            data={
                "email": "CASE@EXAMPLE.COM",
                "name": "別ユーザー",
                "role": User.Role.PARTICIPANT,
                "password1": "SafePassword123!",
                "password2": "SafePassword123!",
            }
        )

        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)


class AccountDeletionFormTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="delete@example.com",
            password="SafePassword123!",
            name="削除対象",
        )

    def test_wrong_password_is_rejected(self):
        form = AccountDeletionForm(
            user=self.user,
            data={"password": "wrong", "confirmation": True},
        )

        self.assertFalse(form.is_valid())
        self.assertIn("password", form.errors)
