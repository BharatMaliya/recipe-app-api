"""
Test the tags API
"""
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Tag, Recipe
from recipe.serializers import TagSerializer

TAGS_URL = reverse('recipe:tag-list')


def detail_url(tag_id):
    """
    Return the URL for the tag detail.
    """
    return reverse('recipe:tag-detail', args=[tag_id])


def create_user(email="user@example.com", password="testpass123"):
    """
    Helper function to create a user.
    """
    return get_user_model().objects.create_user(email, password)


class PublicTagsApiTests(TestCase):
    """
    Test unauthenticated API request.
    """

    def setUp(self):
        """
        Setup the test.
        """
        self.client = APIClient()

    def test_login_required(self):
        """
        Test that login is required for retrieving tags.
        """
        response = self.client.get(TAGS_URL)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateTagsApiTests(TestCase):
    """
    Test the authorized user tags API.
    """

    def setUp(self):
        """
        Setup the test.
        """
        self.user = create_user()
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_retrieve_tags(self):
        """
        Test retrieving tags.
        """
        Tag.objects.create(user=self.user, name="Vegan")
        Tag.objects.create(user=self.user, name="Dessert")

        response = self.client.get(TAGS_URL)
        tags = Tag.objects.all().order_by("-name")
        serializer = TagSerializer(tags, many=True)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def test_tags_limited_to_user(self):
        """
        Test that tags returned are for the authenticated user.
        """
        user2 = create_user(email="user2@example.com", password="testpass123")
        Tag.objects.create(user=user2, name="Fruity")
        tag = Tag.objects.create(user=self.user, name="Comfort Food")

        response = self.client.get(TAGS_URL)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["name"], tag.name)
        self.assertEqual(response.data[0]["id"], tag.id)

    def test_update_tag_successful(self):
        """
        Test updating a tag.
        """
        tag = Tag.objects.create(user=self.user, name="Vegan")
        payload = {"name": "New Tag"}
        url = detail_url(tag.id)
        self.client.patch(url, payload)

        tag.refresh_from_db()
        self.assertEqual(tag.name, payload["name"])

    def test_delete_tag_successful(self):
        """
        Test deleting a tag.
        """
        tag = Tag.objects.create(user=self.user, name="Vegan")
        url = detail_url(tag.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        exists = Tag.objects.filter(id=tag.id).exists()
        self.assertFalse(exists)

    def test_filter_tag_assigned_to_recipe(self):
        """
        Test filtering tags by those assigned to recipes.
        """
        tag1 = Tag.objects.create(user=self.user, name="Breakfast")
        tag2 = Tag.objects.create(user=self.user, name="Lunch")
        recipe = Recipe.objects.create(
            user=self.user,
            title="Coriander eggs on toast",
            time_minutes=10,
            price=Decimal("5.00"),
        )
        recipe.tags.add(tag1)

        response = self.client.get(TAGS_URL, {"assigned_only": 1})

        serializer1 = TagSerializer(tag1)
        serializer2 = TagSerializer(tag2)

        self.assertIn(serializer1.data, response.data)
        self.assertNotIn(serializer2.data, response.data)

    def test_filter_tags_assigned_unique(self):
        """
        Test filtering tags by assigned returns unique items.
        """
        tag = Tag.objects.create(user=self.user, name="Breakfast")
        Tag.objects.create(user=self.user, name="Lunch")
        recipe1 = Recipe.objects.create(
            user=self.user,
            title="Pancakes",
            time_minutes=5,
            price=Decimal("3.00"),
        )
        recipe1.tags.add(tag)
        recipe2 = Recipe.objects.create(
            user=self.user,
            title="Porridge",
            time_minutes=3,
            price=Decimal("2.00"),
        )
        recipe2.tags.add(tag)

        response = self.client.get(TAGS_URL, {"assigned_only": 1})

        self.assertEqual(len(response.data), 1)
