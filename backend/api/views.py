from api.paginations import RecipePagination
from api.permissions import IsAuthorOrReadOnly
from api.serializers import (IngredientSerializer, RecipeCreateSerializer,
                             RecipeReadSerializer,
                             RecipeShopSerializer, SubscribeSerializer,
                             TagSerializer,
                             UserReadSerializer)
from django.conf import settings
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from recipes.models import (Favorite, Ingredient, Recipe, IngredientAmount,
                            ShoppingCart, Tag)
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.permissions import (SAFE_METHODS, IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet
from users.models import Subscribe, User

from api.filters import IngredientFilter, RecipeFilter

CONTENT_TYPE = "text/plain"


class CustomUserViewSet(UserViewSet):
    """Вьюсет для просмотра профиля и создания пользователя."""
    queryset = User.objects.all()
    permission_classes = (IsAuthenticatedOrReadOnly)
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
        permission_classes=(IsAuthenticated),
    )
    def subscribe(self, request, id=None):
        user = self.request.user
        author = get_object_or_404(User, pk=id)

        if request.method == 'POST':
            if user == author:
                return Response({'errors': 'На себя подписаться нельзя!'},
                                status=status.HTTP_400_BAD_REQUEST)
            if Subscribe.objects.filter(user=user, author=author).exists():
                return Response({'errors':
                                 'Вы уже подписаны на этого пользователя!'},
                                status=status.HTTP_400_BAD_REQUEST)

            Subscribe.objects.create(user=user, author=author)
            serializer = SubscribeSerializer(author, context={'request':
                                                              request})

            return Response(serializer.data, status=status.HTTP_201_CREATED)
        elif request.method == 'DELETE':
            subscription = Subscribe.objects.filter(user=user, author=author)
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
        permission_classes=(IsAuthenticated),
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
    permission_classes = (IsAuthorOrReadOnly)
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
        methods=('post', 'delete'),
        permission_classes=(IsAuthenticated)
    )
    def favorite(self, request, **kwargs):
        recipe = get_object_or_404(Recipe, id=kwargs.get('pk'))

        if request.method == 'POST':
            serializer = RecipeShopSerializer(
                recipe, data=request.data, context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            if not Favorite.objects.filter(
                user=request.user, recipe=recipe
            ).exists():
                Favorite.objects.create(user=request.user, recipe=recipe)
                return Response(
                    serializer.data,
                    status=status.HTTP_201_CREATED
                )
            return Response(
                {'errors': 'Рецепт уже в избранном.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if request.method == 'DELETE':
            get_object_or_404(
                Favorite, user=request.user, recipe=recipe
            ).delete()
            return Response(
                {'detail': 'Рецепт успешно удален из избранного.'},
                status=status.HTTP_204_NO_CONTENT,
            )

    @action(
        detail=True,
        methods=['POST', 'DELETE'],
        permission_classes=(IsAuthenticated,),
        pagination_class=None)
    def shopping_cart(self, request, **kwargs):
        recipe = get_object_or_404(Recipe, id=kwargs.get("pk"))
        user = request.user

        if request.method == "POST":
            serializer = RecipeShopSerializer(
                recipe, data=request.data, context={"request": request}
            )
            serializer.is_valid(raise_exception=True)
            if not ShoppingCart.objects.filter(user=user,
                                               recipe=recipe).exists():
                ShoppingCart.objects.create(user=user, recipe=recipe)
                return Response(serializer.data,
                                status=status.HTTP_201_CREATED)
            return Response(
                {"errors": "Рецепт уже в списке"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Проверка существования объекта ShoppingCart
        shopping_cart = ShoppingCart.objects.filter(user=user,
                                                    recipe=recipe).first()
        if not shopping_cart:
            return Response(
                {"errors": "Рецепт не найден в корзине"},
                status=status.HTTP_400_BAD_REQUEST
            )

        shopping_cart.delete()
        return Response(
            {"detail": "Рецепт удален из корзины"},
            status=status.HTTP_204_NO_CONTENT
        )

    @action(
        detail=False,
        methods=['get'],
        permission_classes=(IsAuthenticated,))
    def download_shopping_cart(self, request, **kwargs):
        ingredients = (
            IngredientAmount.objects.filter(

            )
            .values("ingredient__name", "ingredient__measurement_unit")
            .annotate(total_amount=Sum("amount"))
        )

        file_contents = [
            f'{ingredient["ingredient__name"]} - {ingredient["total_amount"]}'
            f'{ingredient["ingredient__measurement_unit"]}.'
            for ingredient in ingredients
        ]

        file_content = "\n".join(file_contents)
        file = HttpResponse(
            "Список покупок:\n" + file_content,
            content_type=CONTENT_TYPE
        )
        file["Content-Disposition"] = f"attachment; \
            filename={settings.FILE_NAME}"

        return file
