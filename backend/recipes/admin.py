from django.contrib import admin
from import_export.admin import ImportExportActionModelAdmin

from recipes.models import (Favorite,
                            Ingredient,
                            IngredientAmount,
                            Recipe,
                            ShoppingCart,
                            Tag)
from users.models import Subscribe, User


@admin.register(Ingredient)
class RecipeIngredientAdmin(ImportExportActionModelAdmin):
    list_display = ('name', 'measurement_unit')
    list_filter = ('name',)
    search_fields = ('name',)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """Админ панель для тегов."""

    list_display = ['name', 'color', 'slug']
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}


class IngredientAmountAdmin(admin.TabularInline):
    model = IngredientAmount
    autocomplete_fields = ('ingredient', )


class RecipeAdmin(admin.ModelAdmin):
    inlines = (IngredientAmountAdmin,)
    list_display = (
        'id',
        'name',
        'author',
        'text',
        'pub_date',
        'favorited_count',
    )
    list_filter = ('author', 'name', 'tags', 'pub_date')

    def favorited_count(self, obj):
        return obj.favorite_recipes.count()

    favorited_count.short_description = 'Favorited Count'


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


class SubscribeAdmin(admin.ModelAdmin):
    list_display = (
        'pk',
        'user',
        'author',
        'pub_date',
    )
    search_fields = ('user',)
    list_filter = ('user',)
    empty_value_display = '-пусто-'


admin.register(IngredientAmount)
admin.site.register(Recipe, RecipeAdmin)
admin.site.register(Favorite)
admin.site.register(ShoppingCart)
admin.site.register(Subscribe)
admin.site.register(User, UserAdmin)
