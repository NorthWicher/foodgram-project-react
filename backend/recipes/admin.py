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


class IngredientAmountAdmin(admin.TabularInline):
    model = IngredientAmount
    autocomplete_fields = ('ingredient', )
    extra = 1


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    inlines = (IngredientAmountAdmin,)
    list_display = (
        'id',
        'name',
        'author',
        'pub_date',
        'text',
    )
    search_fields = (
        'author__username',
        'author__email',
        'name'
    )
    list_filter = (
        'tags',
        'pub_date',
        'author',
        'name',
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

    def favorited_count(self, obj):
        return obj.favorite_recipes.count()

    favorited_count.short_description = 'Favorited Count'


@admin.register(Subscribe)
class SubscribeAdmin(admin.ModelAdmin):
    list_display = (
        'pk',
        'user',
        'author',
    )
    search_fields = (
        'user__username',
        'user__email',
        'user',
    )
    list_fields = (
        'user__username',
        'user__email',
        'user',
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
    list_filter = ('date_joined', 'email', 'first_name')
    empty_value_display = '-пусто-'


admin.site.register(User, UserAdmin)
