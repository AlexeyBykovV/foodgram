FROM python:3.9

WORKDIR /app

COPY requirements.txt .

RUN pip install --upgrade pip

RUN pip install -r requirements.txt --no-cache-dir

RUN apt-get update && apt-get install -y wkhtmltopdf

COPY . .

# CMD ["gunicorn", "--bind", "0.0.0.0:8000", "foodgram_backend.wsgi"]
CMD ["sh", "entrypoint.sh"]