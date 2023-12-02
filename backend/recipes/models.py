from colorfield.fields import ColorField
from django.core import validators
from django.core.validators import MinValueValidator
from django.db import models
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
        models.UniqueConstraint(fields=['user', 'measurement_unit'],
                                name='unique_ingredient')

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
        verbose_name='Уникальный слаг',)

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
        related_name="recipes",
        through="IngredientAmount",
        through_fields=("recipe", "ingredient"),
        verbose_name="Индигриенты.",
        help_text="Индигриенты.",
    )
    tags = models.ManyToManyField(
        Tag,
        related_name='recipes',
        verbose_name='Теги',
    )
    cooking_time = models.PositiveSmallIntegerField(
        validators=(validators.MinValueValidator(1, 'Минимум 1 минута'),),
        verbose_name='Время приготовления',
    )
    pub_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата публикации рецепта',
    )

    class Meta:
        ordering = ('-pub_date',)
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return f'Автор: {self.author.email} рецепт: {self.name}'


class IngredientAmount(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='recipes',
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='ingredients',
    )
    amount = models.PositiveIntegerField(
        'Количество',
        default=1,
        validators=(MinValueValidator(1, 'Минимум 1'),),
    )

    class Meta:
        verbose_name = 'Количество ингредиента'
        verbose_name_plural = 'Количество ингредиентов'

    def __str__(self):
        return (f'В рецепте {self.recipe.name} {self.amount} '
                f'{self.ingredient.measurement_unit} {self.ingredient.name}')


class Favorite(models.Model):
    """Модель избранного."""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favorite_recipes',
        verbose_name='Пользователь',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='favorite_recipes',
        verbose_name='Рецепт',
    )

    class Meta:
        ordering = ['recipe']
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранные'
        unique_together = [['user', 'recipe']]
        models.UniqueConstraint(fields=['user', 'recipe'],
                                name='unique_favorite')

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
        unique_together = [['user', 'recipe']]
        models.UniqueConstraint(fields=['user', 'recipe'],
                                name='unique_shopping')

    def __str__(self):
        return f'Рецепт {self.recipe} в списке покупок у {self.user}'
