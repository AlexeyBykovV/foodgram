from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import CheckConstraint, F, Q, UniqueConstraint

from .validators import username_validator
from core.constants import EMAIL_MAX_LENGTH, USER_MAX_LENGTH
from core.models import AuthorModel


class User(AbstractUser):
    """Модель, описывающая поля пользователя.

    :param email (EmailField): Электронная почта пользователя, уникальная.
    :param username (CharField): Имя пользователя, уникальное, с валидатором.
    :param first_name (CharField): Имя пользователя, необязательное.
    :param last_name (CharField): Фамилия пользователя, необязательная.
    :param avatar (ImageField): Аватар пользователя, необязательный.
    """

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
        """Метакласс для модели User, определяющий параметры модели.

        :param ordering (list): Список полей,
        по которым будет осуществляться сортировка.
        :param verbose_name (str): Человекочитаемое имя модели
        в единственном числе.
        :param verbose_name_plural (str): Человекочитаемое имя модели
        во множественном числе.
        :param constraints (tuple): Ограничения для модели,
        включая уникальные ограничения.

        Ограничения:
            - UniqueConstraint: Гарантирует, что каждая пара
            имя пользователя и электронная почта уникальна.
        """
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
    """Модель, описывающая подписки пользователя.

    :param user (ForeignKey): Пользователь, который подписывается.
    :param author (ForeignKey): Пользователь, на которого подписываются.

    - Метакласс Meta:
    :param default_related_name (str): Имя обратной связи для доступа
    к подпискам.
    :param verbose_name (str): Человекочитаемое имя модели
    в единственном числе.
    :param verbose_name_plural (str): Человекочитаемое имя модели
    во множественном числе.
    :param constraints (tuple): Ограничения для уникальности и проверок.
    """

    user = models.ForeignKey(
        User,
        verbose_name='Подписчик',
        on_delete=models.CASCADE,
        related_name='subscriber',
    )

    class Meta:
        """Мета-класс для модели Subscriptions, определяющий ограничения.

        :param UniqueConstraint: Гарантирует, что каждая пара
        пользователь-автор будет уникальной.
        :param CheckConstraint: Проверяет, что пользователь
        не подписывается на самого себя.
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
        """Возвращает строковое представление подписки."""
        return f'{self.user.username} подписался на {self.author.username}'

    @classmethod
    def get_prefetch(cls, lookup, user):
        """Оптимизация запросов к базе данных.

        Предварительно загружает подписчиков,
        связанных с конкретным пользователем.

        :param cls (type): Класс модели Subscriptions.
        :param lookup (str): Имя поля для предварительной загрузки.
        :param user: Пользователь, для которого загружаются подписчики.
        :return Prefetch: Объект Prefetch для оптимизации запросов.
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
