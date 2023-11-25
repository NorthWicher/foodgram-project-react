from django.core import validators
from django.db import models

from colorfield.fields import ColorField
from foodgram.settings import (MAX_COOKING_TIME, MAX_INGREDIENT_AMOUNT,
                               MIN_COOKING_TIME,
                               MIN_INGREDIENT_AMOUNT)

from users.models import User


class Ingredient(models.Model):
    """Модель ингридиента."""
    name = models.CharField(
        max_length=200,
        verbose_name='Название ингридиента',
    )
    measurement_unit = models.CharField(
        max_length=200,
        verbose_name='Единица измерения',
    )

    class Meta:
        ordering = ('name',)
        verbose_name = 'Ингридиенты'
        verbose_name_plural = 'Ингридиенты'

    def __str__(self):
        return f'{self.name}, {self.measurement_unit}'


class Tag(models.Model):
    """Модель тега."""
    name = models.CharField(
        max_length=200,
        unique=True,
        verbose_name='Название тега',
    )
    color = ColorField(
        verbose_name='Цвет',
        help_text='Выбирите цвет',
        max_length=7,
        unique=True,
    )
    slug = models.SlugField(
        max_length=200,
        unique=True,
        verbose_name='Уникальный слаг',
    )

    class Meta:
        ordering = ('name',)
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name


class Recipe(models.Model):
    """Модель рецепта."""
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='author',
        verbose_name='Автор рецепта',
    )
    name = models.CharField(
        max_length=100,
        verbose_name='Название рецепта',
    )
    image = models.ImageField(
        upload_to='recipes/',
        blank=True,
        verbose_name='Картинка рецепта',
    )
    text = models.TextField(
        help_text='Введите текст рецепта',
        verbose_name='Описание рецепта',
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        related_name='recipes',
        verbose_name='Название ингридиента',
    )
    tags = models.ManyToManyField(
        Tag,
        related_name='recipes',
        verbose_name='Теги',
    )
    cooking_time = models.PositiveSmallIntegerField(
        validators=(
            validators.MinValueValidator(MIN_COOKING_TIME,
                                         f'Минимум {MIN_COOKING_TIME} минута'),
            validators.MaxValueValidator(MAX_COOKING_TIME,
                                         f'Максимум {MAX_COOKING_TIME} минут')
        ),
        verbose_name='Время приготовления'
    )
    pub_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата публикации рецепта',
    )

    class Meta:
        ordering = ('-pub_date',)
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def get_recipes_count(self, obj):
        return obj.author.count()


class IngredientAmount(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='recipe',
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='ingredient',
    )
    amount = models.PositiveIntegerField(
        'Количество',
        default=1,
        validators=(validators.MinValueValidator(MIN_INGREDIENT_AMOUNT,
                    f'Минимум {MIN_INGREDIENT_AMOUNT}'),
                    validators.MaxValueValidator(MAX_INGREDIENT_AMOUNT,
                    f'Максимум {MAX_INGREDIENT_AMOUNT}'),
                    ),
    )

    class Meta:
        ordering = ('id',)
        verbose_name = 'Количество ингредиента'
        verbose_name_plural = 'Количество ингредиентов'

    def __str__(self):
        return (f'В рецепте {self.recipe.name} '
                f'{self.recipe.recipe.count()} '
                f'ингредиентов {self.ingredient.measurement_unit} '
                f'{self.ingredient.name}')


class Favorite(models.Model):
    """Модель избранного."""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='api_favorites',
        verbose_name='Пользователь',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='favorite_recipes',
        verbose_name='Рецепт',
    )

    class Meta:
        ordering = ('recipe',)
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранные'

    def __str__(self):
        return f'Рецепт {self.recipe} в избранном у {self.user}'


class ShoppingCart(models.Model):
    """Модель корзины покупок."""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        related_name='user',
        verbose_name='Пользователь'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='shopping_cart',
        verbose_name='Рецепт'
    )

    class Meta:
        ordering = ('id',)
        verbose_name = 'Покупки'
        verbose_name_plural = 'Покупки'

    def __str__(self):
        return f'Рецепт {self.recipe} в списке покупок у {self.user}'
