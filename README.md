FaceID Project
Система биометрической идентификации на основе Face ID и машинного обучения. Использует Django, PostgreSQL и face_recognition для реализации функционала распознавания лиц.
Требования

Операционная система: macOS, Linux или Windows (с WSL для Windows).
Python: Версия 3.10 (рекомендуется, так как проект тестировался с этой версией).
PostgreSQL: Версия 12 или выше.
Git: Для клонирования репозитория.

Установка
1. Клонируйте репозиторий
Склонируйте проект с GitHub:
git clone https://github.com/BatyrX/aidana_face
cd aidana_face

2. Установите Python 3.10
Убедитесь, что у вас установлена нужная версия Python. Для этого проверьте текущую версию:
python3 --version

Если версия не 3.10, установите её:
На macOS (с Homebrew):
brew install python@3.10

На Ubuntu/Linux:
sudo apt update
sudo apt install python3.10 python3.10-venv python3.10-dev

На Windows:
Скачайте Python 3.10 с официального сайта (https://www.python.org/downloads/release/python-3100/) и установите, добавив Python в PATH.
Проверьте, что Python 3.10 доступен:
python3.10 --version

3. Создайте и активируйте виртуальное окружение
Создайте виртуальное окружение с Python 3.10 и активируйте его:
python3.10 -m venv venv
source venv/bin/activate  # На Windows: venv\Scripts\activate

После активации в терминале должно появиться (venv).
4. Установите зависимости
Установите все необходимые библиотеки из файла requirements.txt:
pip install --upgrade pip
pip install -r requirements.txt

Если возникнут проблемы с установкой (например, с tensorflow или opencv-python на macOS/Windows), установите зависимости вручную:
pip install deepface opencv-python-headless django psycopg2-binary

5. Установите и настройте PostgreSQL
Установка PostgreSQL

macOS:brew install postgresql
brew services start postgresql


Ubuntu/Linux:sudo apt update
sudo apt install postgresql postgresql-contrib
sudo service postgresql start


Windows:Скачайте и установите PostgreSQL с официального сайта (https://www.postgresql.org/download/windows/). Используйте pgAdmin для настройки.

Создайте базу данных

Войдите в PostgreSQL:
psql -U postgres

На Windows может потребоваться указать путь к psql, если он не добавлен в PATH.

Создайте базу данных для проекта:
CREATE DATABASE faceid_project;
CREATE USER faceid_user WITH PASSWORD 'your_password';
ALTER ROLE faceid_user SET client_encoding TO 'utf8';
ALTER ROLE faceid_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE faceid_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE faceid_project TO faceid_user;
\q



Настройте Django для PostgreSQL
Откройте файл настроек Django (например, faceid_project/settings.py) и обновите настройки базы данных:
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'faceid_project',
        'USER': 'faceid_user',
        'PASSWORD': 'your_password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}

6. Примените миграции Django
Запустите миграции для создания таблиц в базе данных:
python manage.py makemigrations
python manage.py migrate

7. Создайте суперпользователя (опционально)
Если тебе нужен доступ к админ-панели Django:
python manage.py createsuperuser

Следуй инструкциям для создания пользователя.
8. Запустите проект
Запусти сервер разработки Django:
python manage.py runserver

Открой браузер и перейди по адресу: http://localhost:8000/.
9. Проверь функционал Face ID

Перейди на страницу регистрации (/register/), чтобы зарегистрировать пользователя.
Затем попробуй авторизоваться через /face_login/, используя веб-камеру для проверки лица.

Устранение неполадок

Ошибка с PostgreSQL: Убедись, что PostgreSQL запущен (brew services start postgresql или sudo service postgresql start), и пользователь/пароль совпадают с настройками в settings.py.
Ошибка с библиотеками: Если pip install не работает для tensorflow или opencv-python, попробуй установить их отдельно или используй opencv-python-headless.
macOS/Linux: Если возникают проблемы с psycopg2, установи зависимости:brew install libpq  # macOS
sudo apt install libpq-dev  # Ubuntu
pip install psycopg2-binary



Дополнительно

Тестирование: Для проверки Face ID используй хорошее освещение и убедись, что веб-камера работает.
Развёртывание: Для продакшена используй gunicorn и настрой веб-сервер (например, Nginx). Не забудь про переменные окружения (.env) для секретных данных.

