from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import UniqueConstraint, CheckConstraint, Q, F

from core.constants import (EMAIL_MAX_LENGTH, USER_MAX_LENGTH)
from core.models import AuthorModel
from .validators import username_validator


class User(AbstractUser):
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

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'username']

    class Meta:
        ordering = ['username']
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        constraints = (
            UniqueConstraint(
                fields=('username', 'email'),
                name='unique_username_email',
            ),
        )


class Subscriptions(AuthorModel):
    """Модель описывающая поля Подписки пользователя."""

    user = models.ForeignKey(
        User,
        verbose_name='Подписчик',
        on_delete=models.CASCADE,
        related_name='subscriber',
    )

    class Meta:
        """Мета-класс класса Follow, определяющий ограничения.

        - UniqueConstraint - ограничение гарантирует,
        что каждая пара пользователь-автор будет уникальной.
        - CheckConstraint - ограничение проверяет,
        что пользователь не подписывается на самого себя.
        """

        default_related_name = 'subscribers'
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        constraints = (
            CheckConstraint(
                check=~Q(user=F('author')),
                name='check_subscriber',
            ),
            UniqueConstraint(
                fields=('user', 'author'),
                name='unique_subscriber',
            ),
        )

    def __str__(self):
        return f'{self.user.username} подписался на {self.author.username}'

    @classmethod
    def get_prefetch(cls, lookup, user):
        """Метод предназначен для оптимизации запросов к базе данных.

        Предварительно загружает подписчиков, связанных
        с конкретным пользователем.
        """
        return models.Prefetch(
            lookup,
            queryset=cls.objects.all().annotate(
                is_subscribed=models.Exists(
                    cls.objects.filter(
                        author=models.OuterRef('author'),
                        user_id=user.id,
                    )
                )
            ),
            to_attr='subscribed',
        )
