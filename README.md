# Фудграм - сайт для обмена рецептами понравившихся блюд.
# Запуск проекта Фудграм в контейнерах и CI/CD с помощью GitHub Actions.

## Описание

«Фудграм» — сайт, на котором пользователи могут публиковать свои рецепты, добавлять чужие рецепты в избранное и подписываться на публикации других авторов.
Зарегистрированным пользователям также доступен сервис «Список покупок». Он позволяет создавать и скачивать список продуктов (.pdf), которые нужно купить для приготовления выбранных блюд.

В проекте настроен деплой проекта черпез СI/CD с помощью GitHub Actions, в ходе которого:
- проверяется код бэкенда в репозитории на соответствие PEP8;
- запускает тесты для фронтенда и бэкенда;
- собирает образы проекта и отправляет их на Docker Hub:
- обновляет образы на сервере и перезапускает приложение при помощи Docker Compose;
- выполняет команды для сборки статики в приложении бэкенда, переносить статику в volume; выполняет миграции;
- извещает вас в Telegram об успешном завершении деплоя.

Используемые библиотеки:
- Django==4.2.12
- django-extra-fields==3.0.2
- django-filter==2.4.0
- djangorestframework==3.15.2
- djoser==2.1.0
- drf-yasg==1.21.7
- psycopg2-binary==2.9.9
- Pillow==9.5.0
- python-dotenv==1.0.0
- gunicorn==20.1.0
- environs==11.0.0
- fpdf==1.7.2
- pdfkit==1.0.0

### Переменные окружения

Пример файла .env c переменными окружения, необходимыми для запуска приложения
```
POSTGRES_USER=foodgram_user
POSTGRES_PASSWORD=foodgram_password
POSTGRES_DB=foodgram_db
DB_HOST=db
DB_PORT=5432
SECRET_KEY=django_secret_key
ALLOWED_HOSTS=hosts
DEBUG=True
```

## Запуск через DockerHUB на удаленном сервере

На удаленном сервере создаем папку проекта `foodgram` и переходим в нее:
```bash
mkdir foodgram
cd foodgram
```

В папку проекта `foodgram` копируем файл `docker-compose.production.yml` и запускаем его:
```bash
sudo docker compose -f docker-compose.production.yml up
```

Будет выполнено:
1. Скачивание образов с DockerHub
2. Развернуты контейнеры отвечающие за `db`, `backend`, `frontend`, `proxy` и созданы volume `pg_data`, `static`, `media`.
3. Установлены необходимые зависимости и выполнены необходимые миграции и сбор статики

## Запуск через GitHub на локальном устройстве

Клонируем репозиторий: 
```bash
git clone git@github.com:AlexeyBykovV/foodgram.git
```

Выполняем запуск:
```bash
sudo docker compose -f docker-compose.yml up
```

Выполняем сбор статистики и миграцию для бэкенда. Статистика фронтенда собирается во время запуска контейнера, после чего он останавливается. 
```bash
sudo docker compose -f [имя-файла-docker-compose.yml] exec backend python manage.py migrate
sudo docker compose -f [имя-файла-docker-compose.yml] exec backend python manage.py collectstatic
sudo docker compose -f [имя-файла-docker-compose.yml] exec backend cp -r /app/collected_static/. /static/static/
```

Проект доступен по адресу:
```bash
http://localhost:8000/
```

## Остановка проекта foodgram

В терминале в котором был запущен проект нажать комбинацию клавищ `Ctrl+С`, либо в доступном терминале ввести команду:
```bash
sudo docker compose -f docker-compose.yml down
```
