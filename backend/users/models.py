from django.contrib.auth.models import AbstractBaseUser
from django.db import models
from django.db.models import UniqueConstraint, CheckConstraint, Q, F

from core.constants import (EMAIL_MAX_LENGTH, USER_MAX_LENGTH)
from core.models import AuthorModel
from .validators import username_validator


class CustomUser(AbstractBaseUser):
    """Модель описывающая поля Пользователя."""

    email = models.EmailField(
        max_length=EMAIL_MAX_LENGTH, verbose_name='email', unique=True,
    )
    username = models.CharField(
        max_length=USER_MAX_LENGTH,
        verbose_name='Имя пользователя',
        unique=True,
        validators=[username_validator],
    )
    first_name = models.CharField(
        max_length=USER_MAX_LENGTH, verbose_name='Имя', blank=True,
    )
    last_name = models.CharField(
        max_length=USER_MAX_LENGTH, verbose_name='Фамилия', blank=True,
    )
    avatar = models.ImageField(
        'Аватар', upload_to='avatars/', blank=True, null=True
    )


class Follow(AuthorModel):
    """Модель описывающая поля Подписки."""

    user = models.ForeignKey(
        CustomUser,
        related_name='following',
        on_delete=models.CASCADE,
        verbose_name='Пользователь',
    )

    class Meta:
        """Мета-класс класса Follow, определяющий ограничения:

        - UniqueConstraint - ограничение гарантирует,
        что каждая пара пользователь-автор будет уникальной.
        - CheckConstraint - ограничение проверяет,
        что пользователь не подписывается на самого себя.
        """

        verbose_name = 'Подписчик'
        verbose_name_plural = 'Подписчики'
        constraints = (
            CheckConstraint(
                check=~Q(user=F('following')),
                name='check_follow',
            ),
            UniqueConstraint(
                fields=('user', 'following'),
                name='unique_follow',
            ),
        )

    def __str__(self):
        return f'{self.user.username!r} подписался на {self.author.username!r}'
