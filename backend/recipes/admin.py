from django.contrib import admin
from import_export.admin import ImportExportActionModelAdmin
from recipes.models import (Favorite, Ingredient, Recipe,
                            ShoppingCart, Tag, IngredientAmount)
from users.models import Subscribe, User


@admin.register(Ingredient)
class IngredientAdmin(ImportExportActionModelAdmin):
    list_display = (
        'name',
        'measurement_unit'
    )
    search_fields = ('name',)
    list_filter = ('measurement_unit',)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = [
        'name',
        'color',
        'slug'
    ]
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}


class IngredientAmountInline(admin.TabularInline):
    model = IngredientAmount
    extra = 0


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'author',
        'pub_date'
    )
    search_fields = (
        'author__username',
        'author__email',
        'name'
    )
    list_filter = (
        'tags',
        'pub_date'
    )


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = (
        'pk',
        'user',
        'recipe'
    )
    search_fields = (
        'user__username',
        'user__email',
        'recipe__name'
    )
    list_filter = ('recipe__tags',)


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = (
        'pk',
        'user',
        'recipe'
    )
    search_fields = (
        'user__username',
        'user__email',
        'recipe__name'
    )
    list_filter = ('recipe__tags',)


@admin.register(Subscribe)
class SubscribeAdmin(admin.ModelAdmin):
    list_display = (
        'pk',
        'user',
        'following'
    )
    search_fields = (
        'user__username',
        'user__email',
        'following__username',
        'following__email'
    )


class UserAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'username',
        'email',
        'first_name',
        'last_name',
        'date_joined'
    )
    search_fields = (
        'email',
        'username',
        'first_name',
        'last_name'
    )
    list_filter = ('date_joined',)
    empty_value_display = '-пусто-'


admin.site.register(User, UserAdmin)
