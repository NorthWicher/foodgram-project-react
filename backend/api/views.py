from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.permissions import (SAFE_METHODS, IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet

from api.filters import IngredientFilter, RecipeFilter
from api.paginations import RecipePagination
from api.permissions import IsAuthorOrReadOnly
from api.serializers import (IngredientSerializer, RecipeCreateSerializer,
                             RecipeReadSerializer, RecipeSerializer,
                             SubscribeSerializer, TagSerializer,
                             UserReadSerializer)
from foodgram.settings import FILE_NAME
from recipes.models import (Favorite, Ingredient, IngredientAmount, Recipe,
                            ShoppingCart, Tag)
from users.models import Subscribe, User


class CustomUserViewSet(UserViewSet):
    """Вьюсет для просмотра профиля и создания пользователя."""
    queryset = User.objects.all()
    permission_classes = (IsAuthenticatedOrReadOnly,)
    pagination_class = RecipePagination

    @action(detail=False, methods=('get',),
            pagination_class=None,
            permission_classes=(IsAuthenticated,))
    def me(self, request):
        serializer = UserReadSerializer(request.user)
        return Response(serializer.data,
                        status=status.HTTP_200_OK)

    @action(
        methods=('POST', 'DELETE'),
        detail=True,
        permission_classes=(IsAuthenticated,),
    )
    def subscribe(self, request, id=None):
        user = self.request.user
        author = get_object_or_404(User, pk=id)
        subscription = Subscribe.objects.filter(user=user, author=author)
        if request.method == 'POST':
            if user == author:
                return Response({'errors': 'На себя подписаться нельзя!'},
                                status=status.HTTP_400_BAD_REQUEST)
            if subscription.exists():
                return Response({'errors':
                                 'Вы уже подписаны на этого пользователя!'},
                                status=status.HTTP_400_BAD_REQUEST)
            Subscribe.objects.create(user=user, author=author)
            serializer = SubscribeSerializer(author, context={'request':
                                                              request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        elif request.method == 'DELETE':
            if subscription.exists():
                subscription.delete()
                return Response({'message':
                                 'Вы больше не подписаны на пользователя'},
                                status=status.HTTP_204_NO_CONTENT)
            return Response({'errors':
                             'Вы не подписаны на этого пользователя!'},
                            status=status.HTTP_400_BAD_REQUEST)
        return Response({'errors': 'Неподдерживаемый метод запроса'},
                        status=status.HTTP_400_BAD_REQUEST)

    @action(
        detail=False,
        permission_classes=(IsAuthenticated,),
        url_path='subscriptions'
    )
    def subscriptions(self, request):
        queryset = User.objects.filter(subscribing__user=request.user)
        pag_queryset = self.paginate_queryset(queryset)
        serializer = SubscribeSerializer(pag_queryset,
                                         many=True,
                                         context={'request': request})
        return self.get_paginated_response(serializer.data)


class IngredientViewSet(ReadOnlyModelViewSet):
    """Вьюсет для просмотра ингредиентов."""
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = (SearchFilter,)
    filterset_class = IngredientFilter
    search_fields = ('^name',)


class TagViewSet(ReadOnlyModelViewSet):
    """Вьюсет для просмотра тегов."""
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class RecipeViewSet(viewsets.ModelViewSet):
    """Вьюсет рецепта.
       Просмотр, создание, редактирование."""
    queryset = Recipe.objects.all()
    permission_classes = (IsAuthorOrReadOnly,)
    serializer_class = RecipeCreateSerializer
    pagination_class = RecipePagination
    filterset_class = RecipeFilter
    filter_backends = (DjangoFilterBackend,)

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def get_serializer_class(self):
        if self.request.method in SAFE_METHODS:
            return RecipeReadSerializer
        return RecipeCreateSerializer

    @action(
        detail=True,
        methods=('post', 'delete',),
        permission_classes=(IsAuthenticated,)
    )
    def favorite(self, request, pk):
        recipe = get_object_or_404(Recipe, id=pk)
        if request.method == 'POST':
            if Favorite.objects.filter(user=request.user,
                                       recipe=recipe).exists():
                return Response({'errors': 'Рецепт уже добавлен!'},
                                status=status.HTTP_400_BAD_REQUEST)
            Favorite.objects.create(user=request.user, recipe=recipe)
            serializer = RecipeReadSerializer(recipe,
                                              context={'request': request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if request.method == 'DELETE':
            fav_rec = Favorite.objects.filter(user=request.user, recipe=recipe)
            if fav_rec.exists():
                fav_rec.delete()
                return Response(
                    {'message': 'Рецепт удален из избранного'},
                    status=status.HTTP_204_NO_CONTENT)
            return Response(
                {'errors': 'Рецепт уже удален!'},
                status=status.HTTP_400_BAD_REQUEST)

    @action(
        detail=True,
        methods=('post', 'delete'),
        permission_classes=(IsAuthenticated,),
        pagination_class=None)
    def shopping_cart(self, request, **kwargs):
        recipe_id = kwargs.get('pk')
        recipe = get_object_or_404(Recipe, id=recipe_id)

        if request.method == 'POST':
            serializer = RecipeSerializer(
                recipe,
                data=request.data,
                context={'request': request})
            serializer.is_valid(raise_exception=True)
            if not ShoppingCart.objects.filter(user=request.user,
                                               recipe=recipe).exists():
                ShoppingCart.objects.create(user=request.user,
                                            recipe=recipe)
                return Response(serializer.data,
                                status=status.HTTP_201_CREATED)
            return Response({'errors': 'Рецепт уже в списке покупок.'},
                            status=status.HTTP_400_BAD_REQUEST)
        if request.method == 'DELETE':
            get_object_or_404(ShoppingCart,
                              user=request.user,
                              recipe=recipe).delete()
            return Response({'detail': 'Рецепт удален из списка покупок.'},
                            status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=('get',),
        permission_classes=(IsAuthenticated,))
    def download_shopping_cart(self, request, **kwargs):
        ingredients = (
            IngredientAmount.objects.filter(

            )
            .values('ingredient__name', 'ingredient__measurement_unit')
            .annotate(total_amount=Sum('amount'))
        )

        file_contents = (
            f'{ingredient["ingredient__name"]} - {ingredient["total_amount"]}'
            f'{ingredient["ingredient__measurement_unit"]}.'
            for ingredient in ingredients
        )

        file_content = '\n'.join(file_contents)
        file = HttpResponse(
            'Список покупок:\n' + file_content,
            content_type='text/plain'
        )
        file['Content-Disposition'] = f'attachment; filename={FILE_NAME}'

        return file
