from django.contrib import admin
from import_export.admin import ImportExportActionModelAdmin
from recipes.models import (Favorite, Ingredient, IngredientAmount, Recipe,
                            ShoppingCart, Tag)
from django.core.exceptions import ValidationError
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


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'author',
        'text',
        'pub_date',
        'favorited_count',
    )
    list_filter = ('author', 'tags', 'pub_date')
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

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        for formset in formsets:
            for form in formset.forms:
                if not form.cleaned_data.get('name'):
                    raise ValidationError('Данное поле обязательное'
                                          'для заполнения')


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
    search_fields = ('user__username',
                     'user__email',
                     'author__username',
                     'author__email')


admin.register(IngredientAmount)
admin.site.register(Recipe, RecipeAdmin)
admin.site.register(Favorite)
admin.site.register(ShoppingCart)
admin.site.register(Subscribe)
admin.site.register(User, UserAdmin)
