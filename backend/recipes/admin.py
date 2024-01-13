from django.contrib import admin
from import_export.admin import ImportExportActionModelAdmin
from recipes.models import (Favorite, Ingredient, Recipe,
                            ShoppingCart, Tag, IngredientAmount)
from django.core.exceptions import ValidationError
from users.models import Subscribe, User


@admin.register(Ingredient)
class RecipeIngredientAdmin(ImportExportActionModelAdmin):
    list_display = ('name', 'measurement_unit')
    list_filter = ('measurement_unit',)
    search_fields = ('name',)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """Админ панель для тегов."""

    list_display = ['name', 'color', 'slug']
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}


class IngredientAmountAdmin(admin.TabularInline):
    model = IngredientAmount
    extra = 1  # Добавляем обязательное поле для заполнения


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'author',
        'pub_date',
        'favorited_count',
    )
    list_filter = ('tags', 'pub_date')
    search_fields = ('author__username', 'name')

    def favorited_count(self, obj):
        return obj.favorite_recipes.count()

    favorited_count.short_description = 'Favorited Count'

    inlines = (IngredientAmountAdmin,)

    def save_model(self, request, obj, form, change):
        if not obj.image:
            raise ValidationError('Поле изображения'
                                  'обязательно для заполнения')
        super().save_model(request, obj, form, change)


class UserAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'username',
        'email',
        'first_name',
        'last_name',
        'date_joined',
    )
    search_fields = ('email', 'username', 'first_name', 'last_name')
    list_filter = ('date_joined', 'email', 'first_name')
    empty_value_display = '-пусто-'


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):  # Исправлено название класса
    list_display = (
        'pk',
        'user',
        'recipe',  # Исправлено название поля
        'pub_date',
    )
    search_fields = ('user__username',  # Исправлено название поля
                     'user__email',  # Исправлено название поля
                     'recipe__name')  # Исправлено название поля
    list_filter = ('user',)  # Исправлено название поля
    empty_value_display = '-пусто-'


admin.site.register(ShoppingCart)
admin.site.register(Subscribe)
admin.site.register(User, UserAdmin)
