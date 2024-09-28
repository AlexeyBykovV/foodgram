import re

from django.core.exceptions import ValidationError


def username_validator(value):
    """Валидация имени пользователя."""
    if value == 'me':
        raise ValidationError(f'{value} служебное имя!')
    if re.findall(r'[^\w.@+-]', value):
        raise ValidationError(['В имени используются недопустимые символы.'])
    return value
