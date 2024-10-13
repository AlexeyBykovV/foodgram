import csv

from django.conf import settings
from django.core.management.base import BaseCommand

from recipes.models import Ingredient


class Command(BaseCommand):
    help = 'Импорт ингредиентов из CSV файла в базу данных.'

    def handle(self, *args, **options):
        """Основной метод команды, вызывающий импорт ингредиентов."""
        self.import_ingredients()

    def import_ingredients(self):
        """Импортирует ингредиенты из CSV файла."""
        file_path = settings.BASE_DIR / 'data/ingredients.csv'
        with open(file_path, 'r', encoding='utf-8') as f:
            self.create_ingredients_from_csv(f)

    def create_ingredients_from_csv(self, file):
        """Создает или получает объекты ингредиентов из CSV файла.

        Аргументы:
        - file: Файловый объект CSV файла, содержащего ингредиенты.
        """
        for row in csv.reader(file):
            name, measurement_unit = row
            Ingredient.objects.get_or_create(
                name=name,
                measurement_unit=measurement_unit,
                defaults={'name': name, 'measurement_unit': measurement_unit}
            )
        self.stdout.write(self.style.SUCCESS('Игредиенты добавлены в БД.'))
