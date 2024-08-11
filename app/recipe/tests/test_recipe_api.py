"""
Tests for the recipe API endpoints.
"""
import tempfile
import os

from PIL import Image

from decimal import Decimal

from django.urls import reverse
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient

from core.models import Recipe, Tag, Ingredient
from recipe.serializers import RecipeSerializer, RecipeDetailSerializer

RECIPES_URL = reverse('recipe:recipe-list')


def detail_url(recipe_id):
    """
    Create and return recipe detail URL.
    """
    return reverse('recipe:recipe-detail', args=[recipe_id])


def image_upload_url(recipe_id):
    """
    Return URL for recipe image upload.
    """
    return reverse('recipe:recipe-upload-image', args=[recipe_id])


def create_user(**params):
    """
    Helper function to create a user.
    """
    return get_user_model().objects.create_user(**params)


def create_recipe(user, **params):
    """
    Helper function to create a recipe.
    """
    defaults = {
        'title': 'Sample recipe',
        'time_minutes': 10,
        'price': Decimal('5.00'),
        'description': 'Sample description',
        'link': 'http://www.sample.com'
    }
    defaults.update(params)

    return Recipe.objects.create(user=user, **defaults)


class PublicRecipeApiTests(TestCase):
    """
    Test unauthenticated recipe API access.
    """

    def setUp(self):
        """
        Setup the test.
        """
        self.client = APIClient()

    def test_auth_required(self):
        """
        Test that authentication is required.
        """
        res = self.client.get(RECIPES_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateRecipeApiTests(TestCase):
    """
    Test authenticated recipe API access.
    """

    def setUp(self):
        """
        Setup the test.
        """
        self.client = APIClient()
        self.user = create_user(
            email='test@example.com',
            password='testpass'
        )

        self.client.force_authenticate(self.user)

    def test_retrieve_recipes(self):
        """
        Test retrieving a list of recipes.
        """
        create_recipe(user=self.user)
        create_recipe(user=self.user)

        res = self.client.get(RECIPES_URL)

        recipes = Recipe.objects.all().order_by('-id')
        serializer = RecipeSerializer(recipes, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_recipes_limited_to_user(self):
        """
        Test retrieving recipes for user.
        """
        user2 = create_user(
            email='test2@example.com',
            password='testpass'
        )
        create_recipe(user=user2)
        create_recipe(user=self.user)

        res = self.client.get(RECIPES_URL)

        recipes = Recipe.objects.filter(user=self.user)
        serializer = RecipeSerializer(recipes, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_view_recipe_detail(self):
        """
        Test viewing a recipe detail.
        """
        recipe = create_recipe(user=self.user)

        url = detail_url(recipe.id)
        res = self.client.get(url)

        serializer = RecipeDetailSerializer(recipe)

        self.assertEqual(res.data, serializer.data)

    def test_create_recipe(self):
        """
        Test creating recipe.
        """
        payload = {
            'title': 'Chocolate cheesecake',
            'time_minutes': 30,
            'price': Decimal('5.90'),
        }

        res = self.client.post(RECIPES_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipe = Recipe.objects.get(id=res.data['id'])
        for key, value in payload.items():
            self.assertEqual(value, getattr(recipe, key))
        self.assertEqual(recipe.user, self.user)

    def test_partial_update_recipe(self):
        """
        Test updating a recipe with patch.
        """
        recipe = create_recipe(user=self.user, title='Beef and mushroom', time_minutes=30, price=Decimal('5.00'))
        payload = {'title': 'Chicken tikka'}

        url = detail_url(recipe.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        recipe.refresh_from_db()
        self.assertEqual(recipe.title, payload['title'])
        self.assertEqual(recipe.user, self.user)

    def test_full_update_recipe(self):
        """
        Test updating a recipe with put.
        """
        recipe = create_recipe(user=self.user, title='Beef and mushroom', time_minutes=30, price=Decimal('5.00'))
        payload = {
            'title': 'Spaghetti carbonara',
            'time_minutes': 25,
            'price': Decimal('7.00'),
        }

        url = detail_url(recipe.id)
        res = self.client.put(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        recipe.refresh_from_db()
        self.assertEqual(recipe.title, payload['title'])
        self.assertEqual(recipe.time_minutes, payload['time_minutes'])
        self.assertEqual(recipe.price, payload['price'])
        self.assertEqual(recipe.user, self.user)

    def test_update_user_return_error(self):
        """
        Test updating user returns error.
        """
        user2 = create_user(email='user2@example.com', password='testpass')
        recipe = create_recipe(user=self.user)

        payload = {'user': user2.id}
        url = detail_url(recipe.id)
        self.client.patch(url, payload)

        recipe.refresh_from_db()
        self.assertEqual(recipe.user, self.user)

    def test_delete_recipe(self):
        """
        Test deleting a recipe.
        """
        recipe = create_recipe(user=self.user)
        url = detail_url(recipe.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Recipe.objects.filter(id=recipe.id).exists())

    def test_delete_other_user_recipe_error(self):
        """
        Test deleting other user's recipe returns error.
        """
        user2 = create_user(email='user2@example.com', password='testpass')
        recipe = create_recipe(user=user2)
        url = detail_url(recipe.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Recipe.objects.filter(id=recipe.id).exists())

    def test_create_recipe_with_new_tags(self):
        """
        Test creating a recipe with new tags.
        """

        payload = {
            'title': 'Avocado lime cheesecake',
            'time_minutes': 60,
            'price': Decimal('20.00'),
            'tags': [{'name': 'Thai'}, {'name': 'Dessert'}]
        }
        res = self.client.post(RECIPES_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipe = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipe.count(), 1)
        recipe = recipe[0]
        self.assertEqual(recipe.tags.count(), 2)
        for tag in payload['tags']:
            exists = recipe.tags.filter(name=tag['name'], user=self.user).exists()
            self.assertTrue(exists)

    def test_create_recipe_with_existing_tags(self):
        """
        Test creating a recipe with existing tags.
        """

        tag1 = Tag.objects.create(user=self.user, name='Indian')
        payload = {
            'title': 'Avocado lime cheesecake',
            'time_minutes': 60,
            'price': Decimal('20.00'),
            'tags': [{'name': 'Indian'}, {'name': 'Breakfast'}]
        }
        res = self.client.post(RECIPES_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipe = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipe.count(), 1)
        recipe = recipe[0]
        self.assertEqual(recipe.tags.count(), 2)
        self.assertIn(tag1, recipe.tags.all())
        for tag in payload['tags']:
            exists = recipe.tags.filter(name=tag['name'], user=self.user).exists()
            self.assertTrue(exists)

    def test_create_tag_on_update(self):
        """
        Test creating a tag on updating recipe.
        """

        recipe = create_recipe(user=self.user)

        payload = {'tags': [{'name': 'Lunch'}]}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        new_tag = Tag.objects.get(user=self.user, name='Lunch')
        self.assertIn(new_tag, recipe.tags.all())

    def test_update_recipe_assign_tag(self):
        """
        Test assigning an existing tag when updating a recipe
        """
        tag_breakfast = Tag.objects.create(user=self.user, name='Breakfast')
        recipe = create_recipe(user=self.user)
        recipe.tags.add(tag_breakfast)

        tag_lunch = Tag.objects.create(user=self.user, name='Lunch')
        payload = {'tags': [{'name': 'Lunch'}]}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(tag_lunch, recipe.tags.all())
        self.assertNotIn(tag_breakfast, recipe.tags.all())

    def test_update_recipe_remove_tag(self):
        """
        Test removing a tag when updating a recipe
        """
        tag_breakfast = Tag.objects.create(user=self.user, name='BreakfastNew')
        recipe = create_recipe(user=self.user)
        recipe.tags.add(tag_breakfast)

        payload = {'tags': []}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertNotIn(tag_breakfast, recipe.tags.all())

    def test_create_recipe_with_new_ingredients(self):
        """
        Test creating a recipe with new ingredients.
        """

        payload = {
            'title': 'Avocado lime cheesecake',
            'time_minutes': 60,
            'price': Decimal('20.00'),
            'ingredients': [{'name': 'Avocado'}, {'name': 'Lime'}]
        }
        res = self.client.post(RECIPES_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipe = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipe.count(), 1)
        recipe = recipe[0]
        self.assertEqual(recipe.ingredients.count(), 2)
        for ingredient in payload['ingredients']:
            exists = recipe.ingredients.filter(name=ingredient['name'], user=self.user).exists()
            self.assertTrue(exists)

    def test_create_recipe_with_existing_ingredients(self):
        """
        Test creating a recipe with existing ingredients.
        """

        ingredient1 = Ingredient.objects.create(user=self.user, name='Avocado')
        payload = {
            'title': 'Avocado lime cheesecake',
            'time_minutes': 60,
            'price': Decimal('20.00'),
            'ingredients': [{'name': 'Avocado'}, {'name': 'Lime'}]
        }
        res = self.client.post(RECIPES_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipe = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipe.count(), 1)
        recipe = recipe[0]
        self.assertEqual(recipe.ingredients.count(), 2)
        self.assertIn(ingredient1, recipe.ingredients.all())
        for ingredient in payload['ingredients']:
            exists = recipe.ingredients.filter(name=ingredient['name'], user=self.user).exists()
            self.assertTrue(exists)

    def test_create_ingredient_on_update(self):
        """
        Test creating an ingredient on updating recipe.
        """

        recipe = create_recipe(user=self.user)

        payload = {'ingredients': [{'name': 'Salt'}]}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        new_ingredient = Ingredient.objects.get(user=self.user, name='Salt')
        self.assertIn(new_ingredient, recipe.ingredients.all())

    def test_update_recipe_assign_ingredient(self):
        """
        Test assigning an existing ingredient when updating a recipe
        """
        ingredient_salt = Ingredient.objects.create(user=self.user, name='Salt')
        recipe = create_recipe(user=self.user)
        recipe.ingredients.add(ingredient_salt)

        ingredient_pepper = Ingredient.objects.create(user=self.user, name='Pepper')
        payload = {'ingredients': [{'name': 'Pepper'}]}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(ingredient_pepper, recipe.ingredients.all())
        self.assertNotIn(ingredient_salt, recipe.ingredients.all())

    def test_update_recipe_remove_ingredient(self):
        """
        Test removing an ingredient when updating a recipe
        """
        ingredient_salt = Ingredient.objects.create(user=self.user, name='Salt')
        recipe = create_recipe(user=self.user)
        recipe.ingredients.add(ingredient_salt)

        payload = {'ingredients': []}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertNotIn(ingredient_salt, recipe.ingredients.all())

    def test_filter_recipes_by_tags(self):
        """
        Test returning recipes with specific tags.
        """
        recipe1 = create_recipe(user=self.user, title='Thai vegetable curry')
        recipe2 = create_recipe(user=self.user, title='Aubergine with tahini')
        tag1 = Tag.objects.create(user=self.user, name='Vegan')
        tag2 = Tag.objects.create(user=self.user, name='Vegetarian')
        recipe1.tags.add(tag1)
        recipe2.tags.add(tag2)
        recipe3 = create_recipe(user=self.user, title='Fish and chips')

        params = {'tags': f'{tag1.id},{tag2.id}'}
        res = self.client.get(RECIPES_URL, params)

        serializer1 = RecipeSerializer(recipe1)
        serializer2 = RecipeSerializer(recipe2)
        serializer3 = RecipeSerializer(recipe3)

        self.assertIn(serializer1.data, res.data)
        self.assertIn(serializer2.data, res.data)
        self.assertNotIn(serializer3.data, res.data)

    def test_filter_recipes_by_ingredients(self):
        """
        Test returning recipes with specific ingredients.
        """
        recipe1 = create_recipe(user=self.user, title='Posh beans on toast')
        recipe2 = create_recipe(user=self.user, title='Chicken cacciatore')
        ingredient1 = Ingredient.objects.create(user=self.user, name='Feta cheese')
        ingredient2 = Ingredient.objects.create(user=self.user, name='Chicken')
        recipe1.ingredients.add(ingredient1)
        recipe2.ingredients.add(ingredient2)
        recipe3 = create_recipe(user=self.user, title='Steak and mushrooms')

        params = {'ingredients': f'{ingredient1.id},{ingredient2.id}'}
        res = self.client.get(RECIPES_URL, params)

        serializer1 = RecipeSerializer(recipe1)
        serializer2 = RecipeSerializer(recipe2)
        serializer3 = RecipeSerializer(recipe3)

        self.assertIn(serializer1.data, res.data)
        self.assertIn(serializer2.data, res.data)
        self.assertNotIn(serializer3.data, res.data)


class ImageUploadTests(TestCase):
    """
    Test for image upload API
    """

    def setUp(self):
        """
        Setup the test.
        """
        self.client = APIClient()
        self.user = create_user(
            email='user@example.com',
            password='testpass'
        )
        self.client.force_authenticate(self.user)
        self.recipe = create_recipe(user=self.user)

    def tearDown(self):
        """
        Clean up the test.
        """
        self.recipe.image.delete()

    def test_upload_image(self):
        """
        Test uploading an image to recipe.
        """

        url = image_upload_url(self.recipe.id)

        with tempfile.NamedTemporaryFile(suffix='.jpg') as image_file:
            img = Image.new('RGB', (10, 10))
            img.save(image_file, format='JPEG')
            image_file.seek(0)
            res = self.client.post(url, {'image': image_file}, format='multipart')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.recipe.refresh_from_db()
        self.assertIn('image',  res.data)
        self.assertTrue(os.path.exists(self.recipe.image.path))

    def test_upload_image_bad_request(self):
        """
        Test uploading an invalid image.
        """

        url = image_upload_url(self.recipe.id)

        res = self.client.post(url, {'image': 'notimage'}, format='multipart')

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
