
from django.core.files.base import ContentFile
from django.db import transaction
from foodgram.settings import (MAX_COOKING_TIME,
                               MAX_INGREDIENT,
                               MIN_COOKING_TIME,
                               MIN_INGREDIENT_AMOUNT,
                               MAX_INGREDIENT_AMOUNT)
from rest_framework import serializers
from rest_framework.relations import SlugRelatedField
from djoser.serializers import UserCreateSerializer, UserSerializer
from users.models import Subscribe, User
from recipes.models import (Favorite, Ingredient,
                            IngredientAmount, Recipe,
                            Tag, ShoppingCart)
import base64
import webcolors


class Base64ImageField(serializers.ImageField):
    """Изображения."""
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')(-1)
            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)

        return super().to_internal_value(data)


class UserCreateSerializer(UserCreateSerializer):
    """Создание пользователя с обязательными полями."""
    class Meta:
        model = User
        fields = ('email',
                  'id',
                  'username',
                  'first_name',
                  'last_name',
                  'password')


class UserReadSerializer(UserSerializer):
    """Страница пользователя."""
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('id', 'email', 'username', 'first_name',
                  'last_name', 'is_subscribed')

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Subscribe.objects.filter(
                user=request.user,
                author=obj).exists()
        return False


class IngredientSerializer(serializers.ModelSerializer):
    """Ингредиенты."""

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class IngredientsInRecipeSerializer(serializers.ModelSerializer):
    """Игредиенты в рецепте."""
    id = serializers.ReadOnlyField(
        source='ingredient.id',
    )
    name = serializers.ReadOnlyField(
        source='ingredient.name',
    )
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit',
    )

    class Meta:
        model = IngredientAmount
        fields = ('id', 'name', 'measurement_unit', 'amount')


class IngredientInRecipeWriteSerializer(serializers.ModelSerializer):
    """Игредиенты в рецепте."""
    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())

    class Meta:
        model = IngredientAmount
        fields = ('id', 'amount')


class TagSerializer(serializers.ModelSerializer):
    """Теги."""
    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'slug')


class RecipeCreateSerializer(serializers.ModelSerializer):
    """Серилизатор для создания рецепта."""
    image = Base64ImageField()
    author = SlugRelatedField(
        slug_field='username',
        read_only=True
    )
    ingredients = IngredientInRecipeWriteSerializer(
        many=True
    )
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True
    )

    class Meta:
        model = Recipe
        fields = ('id', 'ingredients', 'tags',
                  'image', 'name', 'text',
                  'cooking_time', 'author')

    def create_ingredients_amount(self, ingredients, recipe):
        IngredientAmount.objects.bulk_create((
            IngredientAmount(
                ingredient=ingredient.get('id'),
                recipe=recipe,
                amount=ingredient.get('amount')
            )
            for ingredient in ingredients
        ))

    @transaction.atomic
    def create(self, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)
        self.create_ingredients_amount(ingredients, recipe)
        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        recipe = instance
        instance.image = validated_data.get('image', instance.image)
        instance.name = validated_data.get('name', instance.name)
        instance.text = validated_data.get('text', instance.name)
        instance.cooking_time = validated_data.get('cooking_time',
                                                   instance.cooking_time)
        tags = validated_data.get('tags')
        if tags is not None:
            instance.tags.clear()
            instance.tags.set(tags)
        ingredients = validated_data.get('ingredients')
        if ingredients is not None:
            instance.ingredients.clear()
            IngredientAmount.objects.filter(recipe=recipe).delete()
            self.create_ingredients_amount(ingredients, recipe)
        instance.save()
        return instance

    def to_representation(self, instance):
        return RecipeReadSerializer(instance, context={
            'request': self.context.get('request')
        }).data

    def validate(self, obj):
        self.validate_tags(obj)
        self.validate_required_fields(obj)
        self.validate_ingredients_count(obj)
        self.validate_ingredient_uniqueness(obj)
        self.validate_cooking_time(obj)
        self.validate_ingredient_amounts(obj)
        return obj

    def validate_tags(self, obj):
        tags = obj.get('tags', [])
        unique_tags = set(tags)
        if len(tags) != len(unique_tags):
            raise serializers.ValidationError('Теги должны быть уникальными.')

    def validate_required_fields(self, obj):
        required_fields = ('name', 'text', 'cooking_time')
        for field in required_fields:
            if not obj.get(field):
                raise serializers.ValidationError(
                    f'{field} - Обязательное поле.'
                )

    def validate_ingredients_count(self, obj):
        ingredients = obj.get('ingredients', [])
        if not ingredients:
            raise serializers.ValidationError('Нужно минимум 1 ингредиент.')
        if len(ingredients) > MAX_INGREDIENT:
            raise serializers.ValidationError(
                f'Количество ингредиентов не может'
                f'быть больше {MAX_INGREDIENT}.'
            )

    def validate_ingredient_uniqueness(self, obj):
        ingredient_id_list = [item['id'] for item in obj.get('ingredients',
                                                             [])]
        unique_ingredient_id_list = set(ingredient_id_list)
        if len(ingredient_id_list) != len(unique_ingredient_id_list):
            raise serializers.ValidationError('Ингредиенты'
                                              'должны быть уникальны.')

    def validate_cooking_time(self, obj):
        cooking_time = obj.get('cooking_time')
        if cooking_time < MIN_COOKING_TIME or cooking_time > MAX_COOKING_TIME:
            raise serializers.ValidationError(
                f'Время приготовления должно быть'
                f'от {MIN_COOKING_TIME} до {MAX_COOKING_TIME} минут.'
            )

    def validate_ingredient_amounts(self, obj):
        ingredients = obj.get('ingredients', [])
        for ingredient in ingredients:
            amount = ingredient.get('amount')
            if amount is not None:
                if amount < MIN_INGREDIENT_AMOUNT or (
                   amount > MAX_INGREDIENT_AMOUNT):
                    raise serializers.ValidationError(
                        f'Количество ингредиента должно быть в диапазоне'
                        f'от {MIN_INGREDIENT_AMOUNT}'
                        f'до {MAX_INGREDIENT_AMOUNT}.'
                    )
                if amount <= 0:
                    raise serializers.ValidationError(
                        'Количество ингредиента должно быть больше нуля.'
                    )


class IngredientAmount(serializers.ModelSerializer):
    """Серилизатор рецептов."""
    image = Base64ImageField(read_only=True)
    name = serializers.ReadOnlyField()
    cooking_time = serializers.ReadOnlyField()

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class RecipeSerializer(serializers.ModelSerializer):
    """Серилизатор рецептов."""
    image = Base64ImageField(read_only=True)
    name = serializers.ReadOnlyField()
    cooking_time = serializers.ReadOnlyField()

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class IngredientAmountSerializer(serializers.ModelSerializer):
    ingredient = IngredientSerializer()
    recipe = RecipeSerializer()

    class Meta:
        model = IngredientAmount
        fields = ('id', 'ingredient', 'recipe', 'amount')

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['amount'] = (f'В рецепте {instance.recipe.name} '
                                    f'{instance.recipe.ingredients.count()} '
                                    f'ингредиентов'
                                    f'{instance.ingredient.measurement_unit}'
                                    f'{instance.ingredient.name}')
        return representation


class ShoppingCartSerializer(serializers.ModelSerializer):
    """Серилизатор для списка покупок."""

    class Meta:
        model = ShoppingCart
        fields = ('user', 'recipe',)

    def validate(self, data):
        user = data('user',)
        if user.shopping_list.filter(recipe=data('recipe',)).exists():
            raise serializers.ValidationError(
                'Рецепт уже добавлен в корзину'
            )
        return data

    def to_representation(self, instance):
        return RecipeShortSerializer(
            instance.recipe,
            context={'request': self.context.get('request')}
        ).data


class Hex2NameColor(serializers.Field):
    """Преобразует шестнадцатеричный код цвета в соответствующее имя."""
    def to_representation(self, value):
        return value

    def to_internal_value(self, data):
        try:
            data = webcolors.hex_to_name(data)
        except ValueError:
            raise serializers.ValidationError('Для этого цвета нет имени')
        return data


class RecipeReadSerializer(serializers.ModelSerializer):
    """Просмотр рецепта."""
    tags = TagSerializer(
        many=True,
    )
    ingredients = IngredientsInRecipeSerializer(
        many=True,
        source='recipe'
    )
    author = UserReadSerializer()
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'author', 'ingredients',
            'is_favorited',
            'name', 'image', 'text', 'cooking_time',
            'is_in_shopping_cart',
        )

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if request.user.is_anonymous:
            return False
        return Favorite.objects.filter(recipe=obj,
                                       user=request.user).exists()

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        if not request or request.user.is_anonymous:
            return False
        return ShoppingCart.objects.filter(recipe=obj,
                                           user=request.user).exists()


class SubscribeSerializer(serializers.ModelSerializer):
    """
    Данные о пользователе, на которого
    сделана подписка.
    """
    recipes_count = serializers.SerializerMethodField()
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes',
            'recipes_count',
        )

    def get_recipes_count(self, obj):
        return Recipe.objects.filter(author=obj).count()

    def get_is_subscribed(self, obj):
        user = self.context('request',).user
        if user.is_anonymous:
            return False
        return Subscribe.objects.filter(user=user, author=obj).exists()

    def get_recipes(self, obj):
        request = self.context.get('request')
        limit_recipes = request.query_params.get('recipes_limit')
        if limit_recipes is not None:
            recipes = obj.api_favorites.all()[:(int(limit_recipes))]
        else:
            recipes = obj.author.all()
        context = {'request': request}
        return RecipeShortSerializer(recipes, many=True,
                                     context=context).data


class RecipeShortSerializer(serializers.ModelSerializer):
    """Класс сериализатора для представления краткой версии рецепта."""
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'name',
            'image',
            'cooking_time'
        )


class RecipeShopSerializer(serializers.ModelSerializer):
    """Cериализатор для списка покупок."""
    name = serializers.ReadOnlyField()
    cooking_time = serializers.ReadOnlyField()
    image = Base64ImageField(read_only=True)

    class Meta:
        model = Recipe
        fields = ('id',
                  'name',
                  'image',
                  'cooking_time'
                  )
