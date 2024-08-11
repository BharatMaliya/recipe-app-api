"""
Serializers for recipe app
"""

from rest_framework import serializers
from core.models import Tag, Ingredient, Recipe


class IngredientSerializer(serializers.ModelSerializer):
    """
    Serializer for ingredient object.
    """

    class Meta:
        """
        Meta class for serializer.
        """
        model = Ingredient
        fields = ('id', 'name')
        read_only_fields = ('id',)


class TagSerializer(serializers.ModelSerializer):
    """
    Serializer for tag object.
    """

    class Meta:
        """
        Meta class for serializer.
        """
        model = Tag
        fields = ('id', 'name')
        read_only_fields = ('id',)


class RecipeSerializer(serializers.ModelSerializer):
    """
    Serializer for recipe object.
    """
    tags = TagSerializer(many=True, required=False)
    ingredients = IngredientSerializer(many=True, required=False)

    class Meta:
        """
        Meta class for serializer.
        """
        model = Recipe
        fields = (
            'id', 'title', 'time_minutes',
            'price', 'link', 'tags', 'ingredients'
        )
        read_only_fields = ('id',)

    def _get_or_create_tags(self, tags, instance):
        """
        Get or create tags.
        """
        for tag in tags:
            tag_obj, created = Tag.objects.get_or_create(user=instance.user, **tag,)
            instance.tags.add(tag_obj)

    def _get_or_create_ingredients(self, ingredients, instance):
        """
        Get or create ingredients.
        """
        for ingredient in ingredients:
            ingredient_obj, created = Ingredient.objects.get_or_create(user=instance.user, **ingredient)
            instance.ingredients.add(ingredient_obj)

    def create(self, validated_data):
        """
        Create a new recipe.
        """
        tags = validated_data.pop('tags', [])
        ingredients = validated_data.pop('ingredients', [])
        recipe = Recipe.objects.create(**validated_data)
        self._get_or_create_tags(tags, recipe)
        self._get_or_create_ingredients(ingredients, recipe)

        return recipe

    def update(self, instance, validated_data):
        """
        Update a recipe.
        """
        tags = validated_data.pop('tags', None)
        ingredients = validated_data.pop('ingredients', None)
        if tags is not None:
            instance.tags.clear()
            self._get_or_create_tags(tags, instance)

        if ingredients is not None:
            instance.ingredients.clear()
            self._get_or_create_ingredients(ingredients, instance)

        for key, value in validated_data.items():
            setattr(instance, key, value)

        instance.save()
        return instance


class RecipeDetailSerializer(RecipeSerializer):
    """
    Serializer for recipe detail object.
    """

    class Meta(RecipeSerializer.Meta):
        """
        Meta class for serializer.
        """

        fields = RecipeSerializer.Meta.fields + ('description', 'image')


class RecipeImageSerializer(serializers.ModelSerializer):
    """
    Serializer for uploading images to recipes.
    """

    class Meta:
        """
        Meta class for serializer.
        """
        model = Recipe
        fields = ('id', 'image')
        read_only_fields = ('id',)
        extra_kwargs = {
            'image': {'required': True}
        }
