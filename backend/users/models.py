from django.contrib.auth.models import AbstractUser
from django.db import models
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    """Абстрактная модель пользователя."""
    username_validator = UnicodeUsernameValidator()
    username = models.CharField(
        _("username"),
        max_length=150,
        unique=True,
        help_text=_(
            "Required. 150 characters or fewer. Letters, digits and @/./+/-/_."
        ),
        validators=[username_validator],
        error_messages={
            "unique": _("A user with that username already exists."),
        },
    )
    first_name = models.CharField(_("first name"), max_length=150)
    last_name = models.CharField(_("last name"), max_length=150)
    password = models.CharField(_("password"), max_length=150)
    email = models.EmailField(
        _("email address"),
        max_length=254,
        unique=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = [
        'username',
        'first_name',
        'last_name',
    ]

    class Meta:
        ordering = ('id',)
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.username


class Subscribe(models.Model):
    """Модель подписки."""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscribe',
        verbose_name='Подписчик'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscribing',
        verbose_name='Автор'
    )
    created = models.DateField(
        auto_now_add=True,
        verbose_name='Дата подписки'
    )

    class Meta:
        ordering = ('id',)
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        models.UniqueConstraint(fields=['user', 'author'],
                                name='unique_ff')

    def __str__(self):
        return f'Пользователь {self.user} подписался на автора {self.author}'
