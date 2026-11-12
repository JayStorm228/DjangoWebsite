# TRShop — учебный интернет-магазин курсов

Учебный проект: каталог онлайн-курсов с корзиной, заказами, отзывами, админкой и
публичным REST API на Django REST Framework. Интерфейс собран на Bootstrap 5
(тема Start Bootstrap «Creative»).

**Стек:** Django 6.1 · Python 3.12+ · Django REST Framework · drf-spectacular ·
django-filter · SQLite · Bootstrap 5.2 · WhiteNoise.

---

## Возможности

- Каталог курсов: поиск, фильтры по категории/уровню/цене, сортировка, пагинация.
- Страница курса: обложка, описание, метрики, похожие курсы, отзывы с оценками.
- Корзина на сессии, оформление заказа, история покупок («Мои покупки»).
- Регистрация, вход и выход, права доступа к чужим заказам.
- Админка с обложками, инлайнами отзывов и составом заказа.
- Публичный API: каталог, категории, заказы пользователя, OpenAPI-схема и Swagger UI.
- Демо-данные одной командой, 37 автотестов, линтеры и CI.

## Быстрый старт

Нужен Python 3.12 или новее.

```bash
# 1. зависимости (любой способ)
uv sync                  # если установлен uv
# или
python -m venv .venv && source .venv/bin/activate
pip install -e .         # либо: pip install django djangorestframework ...

# 2. настройки окружения
cp .env.example .env

# 3. база и демо-данные
python manage.py migrate
python manage.py seed_demo

# 4. запуск
python manage.py runserver
```

Сайт: <http://127.0.0.1:8000/> · API-документация: <http://127.0.0.1:8000/api/docs/> ·
админка: <http://127.0.0.1:8000/admin/>.

### Демо-аккаунты

| Логин | Пароль | Роль |
|---|---|---|
| `demo` | `demo12345` | покупатель с одним заказом |
| `admin` | `admin12345` | администратор (staff) |
| `anna`, `ivan`, `maria` | `demo12345` | авторы отзывов |

### Переменные окружения

Все настройки читаются из окружения или `.env` (шаблон — `.env.example`):

| Переменная | По умолчанию | Назначение |
|---|---|---|
| `DJANGO_SECRET_KEY` | dev-ключ | секретный ключ Django |
| `DJANGO_DEBUG` | `1` | `0` для продакшена |
| `DJANGO_ALLOWED_HOSTS` | `*` при `DEBUG=1` | список хостов через запятую |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | `https://*.e2b.app` | домены для POST-форм |
| `DJANGO_EMAIL_BACKEND` | console | backend отправки писем |

## API

Базовый URL: `/api/v1/`. Чтение доступно без авторизации, заказы — только владельцу
токена. Интерактивная документация: `/api/docs/`, схема OpenAPI: `/api/schema/`.

| Метод | Endpoint | Описание |
|---|---|---|
| `GET` | `/api/v1/courses/` | список курсов (пагинация, поиск, фильтры) |
| `GET` | `/api/v1/courses/{slug}/` | курс по slug |
| `GET` | `/api/v1/categories/` | категории с числом курсов |
| `GET` | `/api/v1/orders/` | заказы текущего пользователя |
| `POST` | `/api/v1/auth/token/` | получить токен по логину и паролю |

Параметры каталога: `search`, `category__slug`, `level`, `price__gte`, `price__lte`,
`ordering` (`price`, `-price`, `created_at`, `student_qty`, `title`), `page`, `page_size`.

```bash
# каталог
curl "http://127.0.0.1:8000/api/v1/courses/?search=django&ordering=price"

# токен и заказы
TOKEN=$(curl -s -X POST http://127.0.0.1:8000/api/v1/auth/token/ \
  -d "username=demo&password=demo12345" | python -c "import sys,json;print(json.load(sys.stdin)['token'])")
curl -H "Authorization: Token $TOKEN" http://127.0.0.1:8000/api/v1/orders/
```

## Тесты и качество кода

```bash
pytest                      # 37 тестов
ruff check .                # линтер
ruff format --check .       # форматирование
djlint --lint templates     # линтер шаблонов
coverage run -m pytest && coverage report
```

CI (GitHub Actions) запускает линтеры, шаблонный линтер, тесты и проверку миграций
на каждый push и pull request.

## Структура проекта

```text
config/            настройки, корневые URL, главная страница, обработчики 404/500
shop/              модели, представления, формы, корзина, админка, тесты
  management/commands/seed_demo.py   демо-данные
  templatetags/shop_tags.py          русская плюрализация
api/               DRF: сериализаторы, viewset-ы, маршруты, пагинация, тесты
templates/         base, домашняя, каталог, курс, корзина, заказы, авторизация
static/            тема (styles.css + theme.css), скрипты, изображения
docs/AUDIT.md      аудит исходной версии проекта и план развития
```

## Деплой (кратко)

1. `DJANGO_DEBUG=0`, задайте `DJANGO_SECRET_KEY` и `DJANGO_ALLOWED_HOSTS`.
2. `python manage.py collectstatic` — WhiteNoise раздаст статику.
3. Запуск через gunicorn: `gunicorn config.wsgi:application`.
4. Медиа-файлы (`media/`) вынесите в объектное хранилище или отдавайте через nginx.
5. Для продакшена замените SQLite на PostgreSQL и включите HTTPS-настройки.

## Лицензия и атрибуция

Учебный код проекта распространяется свободно. Визуальная тема основана на
[Start Bootstrap «Creative»](https://startbootstrap.com/theme/creative) (MIT,
Copyright © 2013–2023 Start Bootstrap LLC); текст лицензии — `static/assets/LICENSE-creative.txt`.
Bootstrap © The Bootstrap Authors, MIT. Django © Django Software Foundation, BSD.
