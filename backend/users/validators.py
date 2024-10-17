import re

from django.core.exceptions import ValidationError


def username_validator(value):
    """Валидация имени пользователя.

    Проверяет, соответствует ли имя пользователя заданным критериям:
    - Имя не должно быть 'me'.
    - Имя должно содержать только допустимые символы: буквы, цифры,
    а также символы '.', '@', '+', '-' (в соответствии с правилами).

    :param value (str): Имя пользователя для валидации.
    :raises ValidationError: Если имя пользователя является служебным (например, 'me') или содержит недопустимые символы.
    :return: Проверенное имя пользователя, если оно валидно.
    """
    if value == 'me':
        raise ValidationError(f'{value} служебное имя!')
    if re.findall(r'[^\w.@+-]', value):
        raise ValidationError(['В имени используются недопустимые символы.'])
    return value
