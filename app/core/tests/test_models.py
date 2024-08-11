"""
Tests for the models of the core app.
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from decimal import Decimal
from unittest.mock import patch

from core import models


def create_user(email='user@example.com', password='testpass123'):
    """
    Helper function to create a user.
    """

    return get_user_model().objects.create_user(email, password)


class ModelTests(TestCase):
    """
    Test the core app models.
    """

    def test_create_user_with_email_successful(self):
        """
        Test creating a new user with an email is successful
        """

        email = 'test@example.com'
        password = 'testpass123'
        user = get_user_model().objects.create_user(
            email=email,
            password=password
        )

        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))

    def test_new_user_email_normalized(self):
        """
        Test the email for a new user is normalized
        """

        sample_email = [
            ['test1@EXAMPLE.com', 'test1@example.com'],
            ['Test2@Example.com', 'Test2@example.com'],
            ['TEST3@EXAMPLE.COM', 'TEST3@example.com'],
            ['test4@Example.COM', 'test4@example.com'],
        ]

        for email, expected in sample_email:
            user = get_user_model().objects.create_user(email, 'test123')
            self.assertEqual(user.email, expected)

    def test_new_user_without_email_raises_error(self):
        """
        Test creating user without email raises error
        """

        with self.assertRaises(ValueError):
            get_user_model().objects.create_user('', 'test123')

    def test_create_new_superuser(self):
        """
        Test creating a new superuser
        """

        user = get_user_model().objects.create_superuser(
            'test@example.com',
            'test123'
        )

        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)

    def test_create_recipe(self):
        """
        Test creating a new recipe
        """
        user = get_user_model().objects.create_user(
            'test@example.com',
            'test123'
        )
        recipe = models.Recipe.objects.create(
            user=user,
            title='Steak and mushroom sauce',
            time_minutes=5,
            price=Decimal('5.50'),
            description='This is a test description'
        )

        self.assertEqual(str(recipe), recipe.title)

    def test_create_tag(self):
        """
        Test creating a new tag
        """
        user = create_user()
        tag = models.Tag.objects.create(user=user, name='Vegan')

        self.assertEqual(str(tag), tag.name)

    def test_create_ingredient(self):
        """
        Test creating a new ingredient
        """
        user = create_user()
        ingredient = models.Ingredient.objects.create(user=user, name='Cucumber')

        self.assertEqual(str(ingredient), ingredient.name)

    @patch('core.models.uuid.uuid4')
    def test_recipe_file_name_uuid(self, mock_uuid):
        """
        Test that image is saved in the correct location
        """
        uuid = 'test-uuid'
        mock_uuid.return_value = uuid
        file_path = models.recipe_image_file_path(None, 'myimage.jpg')

        exp_path = f'uploads/recipe/{uuid}.jpg'
        self.assertEqual(file_path, exp_path)
