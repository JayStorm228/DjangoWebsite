# Аудит проекта TRShop (DjangoWebsite)

**Ветка:** `arena/738ee670-djangowebsite` · **Коммит:** `67307f2 feat: added API(Beta ver)`
**Стек:** Django 6.1.2 · django-tastypie 0.15.1 · Python ≥ 3.14 · SQLite · Bootstrap 5 (локально)
**Дата аудита:** 12.11.2026

---

## Статус на 12.11.2026 (после первой итерации)

Ниже перечислены решения, которые уже реализованы в проекте. Сам аудит оставлен
как история: он описывает исходное состояние коммита `67307f2`.

| Проблема | Решение | Статус |
|---|---|---|
| P0-1 `ALLOWED_HOSTS` / preview | env-настройки, `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS` | ✅ |
| P0-2 конфликт версий | Django 6.1 + DRF, `requires-python = ">=3.12"`, tastypie удалён | ✅ |
| P0-3 `?category=abc` → 500 | безопасный разбор фильтров + тесты на мусорные параметры | ✅ |
| P0-4 API падает / нет валидации | каталог API только для чтения, заказы — только владельцу; сериализаторы DRF | ✅ |
| P0-5 `category_id` = название | вложенная категория + корректный slug в ответе | ✅ |
| P0-6 удаление чужих курсов | публичный API read-only, запись — через админку | ✅ |
| P0-7 секреты в Git | `SECRET_KEY`/`DEBUG` из окружения, `.env.example` | ✅ |
| P0-8 дрейф миграций | `DEFAULT_AUTO_FIELD`, новая чистая миграция | ✅ |
| P1-1 цена во float | `DecimalField`, вывод в рублях, старая цена и скидка | ✅ |
| P1-2 поиск/пагинация/N+1 | `icontains`, `select_related`, `annotate`, пагинация по 9, сортировки | ✅ |
| P1-3 пустая карточка курса | новая страница: обложка, описание, отзывы, метрики, CTA | ✅ |
| P1-4 404 и маршруты | `get_object_or_404`, slug-URL, страницы 404/500 | ✅ |
| P1-5 «Buy» ничего не делает | корзина, оформление, заказы, «Мои покупки», отзывы | ✅ |
| P1-6 нет API | DRF: каталог, категории, заказы, токены, OpenAPI и Swagger | ✅ |
| P1-7 визуал | тема Start Bootstrap + `theme.css`, карточки, обложки | ✅ |
| P1-8 плюрализация и языки | `ru-ru`, фильтр `ru_plural`, единый русский интерфейс | ✅ |
| P1-9 админка и демо-данные | настроенная админка + `seed_demo` | ✅ |
| P2-1 тесты | 37 тестов (pytest-django) | ✅ |
| P2-2 CI и линт | GitHub Actions, ruff/ruff format/djlint/migrations/pytest | ✅ |
| P2-3 README | полная документация и быстрый старт | ✅ |
| P2-4 медиа | `MEDIA_URL/MEDIA_ROOT`, `ImageField`, Pillow | ✅ |
| P2-5 структура API | `serializers.py`, `views.py`, `urls.py`, `pagination.py` | ✅ |
| P2-6 модели | verbose_name, auto_now_add, related_name, индексы, ограничения | ✅ |
| P2-7 настройки | env, логирование, WhiteNoise, прод-безопасность | ✅ |
| P2-8 шаблоны | чистое наследование, include-ы, единый base | ✅ |
| P2-9 API-контракт | фильтры, поиск, сортировка, схема OpenAPI | ✅ |
| P2-10 API-ключи | токены DRF и endpoint `/api/v1/auth/token/` | ✅ |
| P2-11 доступность/SEO | метаописания, семантика, адаптивные карточки | ✅ |
| P2-12 `main.py` | удалён | ✅ |
| P3 стиль | ruff/форматирование/мелочи | ✅ |

**Что осталось как осознанный выбор / следующий шаг:** PostgreSQL и Docker для
продакшена, CORS (если появятся браузерные клиенты на других доменах), оплата
через реальный платёжный шлюз, кэширование каталога, загрузка видео/материалов
курса, письма и сброс пароля с реальным SMTP.

---

## 0. Как проверял

| Проверка | Команда | Результат |
|---|---|---|
| Системные проверки Django | `manage.py check` | 4 предупреждения `W042` (auto-created PK) |
| Дрейф миграций | `makemigrations --check --dry-run` | **требуется новая миграция `0002_alter_*_id`** |
| Линтер Python | `ruff check .` | 5 ошибок (4 автофиксимых) |
| Форматирование Python | `ruff format --check .` | 5 файлов не отформатированы |
| Линтер шаблонов | `djlint --lint --profile django templates` | 0 ошибок (хорошо), но форматирование отличается |
| Функциональный прогон | Django test client + 3 тестовых курса, ~20 запросов | найдены падения ниже |
| API | GET/POST/DELETE с `ApiKey` | найдены 5 дефектов |
| Тесты | `shop/tests.py`, `api/tests.py` | **тестов нет вообще** |

**Ограничение аудита:** в песочнице доступен только Python 3.11, а Django 6.1.2 требует ≥ 3.12, поэтому
прогон выполнялся на Django 5.2.19. Все найденные дефекты находятся в коде проекта (URL, views, шаблоны,
модели, ресурсы API) и воспроизводятся на обеих версиях. Специфичные для 6.1 вещи (например, `MAILERS`)
не проверялись. Визуал оценивался по шаблонам и CSS, без браузера.

---

## 1. Общая картина

Проект — аккуратно начатый, но **очень ранний каркас**: есть 2 модели, список и карточка курса,
админка, 404-страница, «бета»-API. Всё остальное — впереди.

**Что уже сделано хорошо**

- Правильная структура проектов Django: `config` + приложения `shop` и `api`, неймспейсы URL (`shop:index`, `api/v1/`).
- Есть миграция, `.gitignore` с секретами и `db.sqlite3`, конфиги `ruff`/`djlint`/`prettier`, рекомендации VS Code.
- Осмысленные имена, шаблонное наследование (`base.html` → `shop/base.html`), отдельная 404-страница.
- Bootstrap подключён локально (не зависит от CDN), `djlint` проходит без ошибок.

**Главные выводы**

1. **Проект в текущем виде не запустится** у большинства людей: `requires-python = ">=3.14"`, а `tastypie` официально поддерживает Django только до 5.2.
2. **API «бета» сломано в 5 местах**: падает на POST без `category_id`, принимает отрицательные цены, отдаёт название категории вместо её id, позволяет любому владельцу ключа удалить любой курс.
3. **Сайт нельзя открыть по внешнему адресу**: `ALLOWED_HOSTS = []` + `DEBUG = True` → `DisallowedHost` для всего, кроме `localhost`.
4. **Магазина по сути нет**: кнопка «Buy» ничего не делает, нет корзины, заказов, пользователей, изображений и описаний курсов.
5. **Внешнего API нет**: текущее API — собственное, «наружу». Интеграции с сервисами (платежи, курсы валют, контент) нет ни в каком виде.
6. **Визуал — дефолтный Bootstrap**: 8.4 МБ вендорных файлов (44 файла, 22 source-map), при этом ни одной своей CSS-строки, ни одной картинки.

**Сводка по приоритетам**

| Приоритет | Кол-во | Смысл |
|---|---|---|
| **P0** — критично | 8 | ломает запуск, безопасность, API, деньги |
| **P1** — серьёзно | 9 | нет обязательной функциональности магазина |
| **P2** — средне | 12 | качество кода, архитектура, поддерживаемость |
| **P3** — мелочи | 10 | стиль, косметика |

---

## 2. P0 — критичные проблемы

### P0-1. Сайт недоступен по внешнему адресу (`ALLOWED_HOSTS`)

**Где:** `config/settings.py:28` (`ALLOWED_HOSTS = []`), `:26` (`DEBUG = True`).
**Симптом:** любой запрос с `Host`, отличным от `localhost`/`127.0.0.1`, отдаёт `400 DisallowedHost`.
Проверено: запрос с `HTTP_HOST: testserver` падает с `django.core.exceptions.DisallowedHost` — то же будет
с preview-доменом вида `1234-xxx.e2b.app` и с любым деплоем. Сайт виден только на своей машине.
**Причина:** при пустом `ALLOWED_HOSTS` и `DEBUG=True` Django разрешает только localhost-варианты.

**Варианты решения**

- **A. Переменные окружения (рекомендую).** `ALLOWED_HOSTS` из `DJANGO_ALLOWED_HOSTS` (через запятую), в dev — `["*"]` или `[".localhost", "127.0.0.1", ".e2b.app"]`; `SECRET_KEY` и `DEBUG` — тоже из env. Плюс `CSRF_TRUSTED_ORIGINS` для https-preview, иначе следующие формы с POST будут падать с 403.
- **B. `django-environ` / `pydantic-settings`.** То же, но с типизацией и `.env`-файлом; +1 зависимость, зато удобно и «по-взрослому».
- **C. Разделить настройки:** `config/settings/base.py`, `dev.py`, `prod.py` и `DJANGO_SETTINGS_MODULE` по окружению. Больше файлов, зато явное разделение dev/prod.

> В любом варианте: добавить `.env.example` (он уже разрешён в `.gitignore`) и `SECRET_KEY` из окружения.

---

### P0-2. Конфликт версий: проект не устанавливается

**Где:** `pyproject.toml:6` (`requires-python = ">=3.14"`), `:8` (`django>=6.1.2`), `:9` (`django-tastypie>=0.15.1`), `uv.lock`.
**Симптом и факты:**

- Django 6.1.2/6.1.3 требуют **Python ≥ 3.12**, а не 3.14. Требование `>=3.14` без причины отсекает Python 3.12/3.13 — на них проект просто не поставится (`uv sync` откажется), хотя Django бы работал.
- `django-tastypie 0.15.1` (единственный релиз, февраль 2025) заявляет поддержку **Django 4.2–5.2**. Django 6.x официально не поддерживается — риск, что `tastypie` упадёт на импорте/рантайме.
- В `uv.lock` зафиксирован Django **6.1.2**, хотя на PyPI уже **6.1.3** (патч с исправлениями безопасности/багов). Лок «протух».
- В песочнице с Python 3.11 установка `django==6.1.2` невозможна в принципе.

**Варианты решения**

- **A. Django 5.2 LTS + DRF + Python ≥ 3.12 (рекомендую).** LTS до 2028, максимальная совместимость библиотек, DRF — индустриальный стандарт (полезнее для учебного проекта, чем tastypie). Нужно переписать `api/` (30 строк) — недорого.
- **B. Django 6.1 + DRF + Python ≥ 3.13.** Современно, но 6.1 — не LTS, и совместимость DRF с 6.1 надо проверять отдельно. Оставить как второй шаг после стабилизации.
- **C. Оставить tastypie, но зафиксировать Django 5.2 и Python 3.12/3.13.** Минимум изменений в коде, но стек тупиковый: tastypie фактически не развивается, документации и примеров мало, на рынке его не спрашивают.

> Дополнительно: `description = "Add your description here"` → описание проекта; `name = "django-course"` → `trshop`; зафиксировать `django>=5.2,<5.3` (или `~=6.1.3`) и обновить `uv.lock`.

---

### P0-3. `?category=abc` → 500 (падение страницы)

**Где:** `shop/views.py:13-14`.
**Воспроизведение:** `GET /shop/?category=abc` → `ValueError: Field 'id' expected a number but got 'abc'.`
Пользователь (или бот, или битая ссылка) получает 500 вместо «ничего не найдено».
**Причина:** значение из GET без валидации передаётся в `filter(category=<строка>)`.

**Варианты решения**

- **A. Быстрый фикс:** привести к `int` в `try/except (TypeError, ValueError)` → вернуть пустой queryset и сообщение «категория не найдена».
- **B. Django Form для фильтра (рекомендую):** `CourseFilterForm` с `ChoiceField` по категориям и `CharField` для названия; `form.is_valid()` сам отсеет мусор, а в шаблоне можно показать ошибки. Заодно переиспользуется для API/тестов.
- **C. `django-filter`:** декларативные фильтры (`title__icontains`, `category__id`, `price__gte/lte`), меньше кода, +1 зависимость; хорошо сочетается с DRF.

---

### P0-4. API падает на POST и не валидирует данные

**Где:** `api/models.py:25-27` (`hydrate`), `Meta` без `validation`.
**Воспроизведение (ключ `ApiKey`):**

| Запрос | Результат |
|---|---|
| `POST /api/v1/courses/` без `category_id` | **500** `KeyError: 'category_id'` |
| `POST ... category_id=999` | **500** `IntegrityError: FOREIGN KEY constraint failed` |
| `POST ... price=-500, student_qty=-42` | **201 Created** — отрицательные цена и число студентов сохранены |
| `POST ... title` из 1000 символов | **201 Created** — превышение `max_length=255` не проверяется |

**Причина:** `hydrate` жёстко читает ключ из `bundle.data`, исключения не перехватываются, `full_clean()`
не вызывается, валидаторов на полях нет.

**Варианты решения**

- **A. Минимальный фикс (30 минут):** `bundle.data.get("category_id")`, проверка существования категории, `bundle.obj.full_clean()` в `obj_create`, `try/except (KeyError, ValueError, ValidationError, IntegrityError)` → `BadRequest`.
- **B. Полноценная валидация в текущем стеке:** кастомный `Validation` + `clean()` на ресурсе, `Meta.validation`, аккуратные `ApiField`-ы, `always_return_data = True` (сейчас POST отвечает пустым телом).
- **C. DRF-сериализаторы (рекомендую вместе с P0-2/вариант A):** `ModelSerializer` с `validate_price`, `PrimaryKeyRelatedField`, статусы 400/404 «из коробки», автогенерируемая схема OpenAPI. Больше работы один раз, но дальше всё проще и понятнее.

---

### P0-5. API отдаёт название категории вместо `id`

**Где:** `api/models.py:29-31`.
**Воспроизведение:** `GET /api/v1/courses/` → `"category_id": "Python"` вместо `"category_id": 1`.
Клиент не может связать курс с категорией; поле называется `_id`, но содержит строку-название.
Дополнительно: `bundle.obj.category` тянет объект из БД на каждый курс (N+1: 5 запросов на 3 курса).

**Варианты решения**

- **A. Исправить на `bundle.obj.category_id`** (одна строка) — контракт снова осмысленный.
- **B. Отдавать оба поля (рекомендую):** `category` как URI связанного ресурса (`/api/v1/categories/1/`) + `category_id` числом; `select_related("category")` в `Meta.queryset` — решает и N+1, и удобство клиента.
- **C. Полный переход на DRF:** `PrimaryKeyRelatedField`/`SlugRelatedField` — те же данные, но с валидацией и без ручного `dehydrate`.

---

### P0-6. Любой владелец API-ключа может удалить любой курс

**Где:** `api/models.py:21-23` (`allowed_methods = ["get", "post", "delete"]`, `authorization = Authorization()`), `api/auth.py:6`.
**Воспроизведение:** создал обычного пользователя + `ApiKey`, отправил `DELETE /api/v1/courses/1/` → **204 No Content**, курс удалён. Никаких ролей и проверок владельца нет.
**Причина:** `tastypie.authorization.Authorization` разрешает всё аутентифицированному пользователю; CSRF для API отключён, так что достаточно одного ключа.

**Варианты решения**

- **A. Сделать API только для чтения (рекомендую для учебного магазина):** `allowed_methods = ["get"]`, `authorization = ReadOnlyAuthorization()`. Запись — через админку. Самый безопасный и понятный вариант.
- **B. Запись только для staff:** `DjangoAuthorization()` + кастомная `StaffOnlyAuthorization` (проверка `request.user.is_staff`). Полезно, если нужен «редакторский» API.
- **C. Полноценные права:** DRF + `IsAdminUser`/`IsAuthenticatedOrReadOnly`, JWT, владение объектами (`Order.user`). Правильно для боевого магазина, но это отдельная итерация.

---

### P0-7. Секреты и режим отладки в репозитории

**Где:** `config/settings.py:23` (`SECRET_KEY = "django-insecure-qqlal!..."`), `:26` (`DEBUG = True`).
**Риск:** ключ в Git (его надо считать скомпрометированным и сменить), `DEBUG=True` на публичном адресе
показывает трейсбеки, SQL-запросы, настройки и файлы. Плюс `MAILERS` с console-backend — письма никуда не уходят.

**Варианты решения**

- **A. Env-переменные + `.env.example` (рекомендую):** `SECRET_KEY = os.environ["DJANGO_SECRET_KEY"]`, `DEBUG = os.getenv("DJANGO_DEBUG", "0") == "1"`; локально — `.env` (уже в `.gitignore`).
- **B. `django-environ`** — чтение `.env` без ручного парсинга.
- **C. Отдельный `local_settings.py`** (уже в `.gitignore`), импортируемый в конце `settings.py`; быстро, но менее прозрачно.

> Для продакшена добавить: `SECURE_HSTS_*`, `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`, `X_FRAME_OPTIONS`, `SECURE_PROXY_SSL_HEADER`, WhiteNoise/`collectstatic`, gunicorn.

---

### P0-8. Модели и миграции расходятся

**Где:** `shop/apps.py:4-5`, `api/apps.py:4-5` (нет `default_auto_field`), `config/settings.py` (нет `DEFAULT_AUTO_FIELD`).
**Симптом:** `manage.py check` → 4 предупреждения `W042`; `makemigrations --check` → «Migrations for 'shop': 0002_alter_category_id_alter_course_id».
Миграция `0001` создаёт `BigAutoField`, а модели в рантайме используют `AutoField` — расхождение будет
копиться при каждом `makemigrations`, а `CI` с `--check` будет красным.

**Варианты решения**

- **A. `DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"` + сгенерировать `0002` (рекомендую).** Явно, совпадает с `0001`, предупреждения исчезают.
- **B. Прописать `default_auto_field = "django.db.models.BigAutoField"` в каждом `AppConfig`.** Локально по приложениям, полезно, если приложения будут переиспользоваться.
- **C. Откатить `0001` на `AutoField`.** Не рекомендую: `BigAutoField` — дефолт новых проектов и лучше для роста таблиц.

---

## 3. P1 — серьёзные проблемы

### P1-1. Цена хранится в `FloatField`

**Где:** `shop/models.py:16`, API/UI отдают `299.96999999999997`.
**Почему плохо:** для денег нужен `DecimalField(max_digits=10, decimal_places=2)`; float даёт хвосты,
ошибки округления и несовпадение сумм в заказах. Валюты тоже нет.
**Решения:** **A (рекомендую)** — `DecimalField` + `currency` (по умолчанию `RUB`) + форматирование в шаблоне
(`{{ course.price|floatformat:2 }} ₽` или `intcomma`); миграция + правка API. **B** — оставить float, но
форматировать вывод (быстро, проблему не решает). **C** — `django-money` (отдельный тип `MoneyField`), плюс
зависимость и особенности в SQLite.

### P1-2. Поиск, пагинация и N+1 на каталоге

**Где:** `shop/views.py:8-15`.
**Факты:** поиск по названию — **точное** совпадение (`title=title`), поэтому `?title=Курс` не находит «Курс 1»;
пагинации нет (все курсы в одном ответе); `select_related` нет — 6 запросов на 3 курса, на 300 будет ~300;
сортировки нет (`Meta.ordering` отсутствует → порядок «как БД положит»).
**Решения:** **A (рекомендую)** — `title__icontains`, `select_related("category")`, `Paginator`/`ListView`
с `paginate_by=12`, `Meta.ordering = ["-created_at"]`, счётчик через уже загруженный queryset. **B** —
`django-filter` + `ListView` (декларативно, +1 зависимость). **C** — `django-tables2` (таблица с сортировкой
из коробки, но тяжелее и меньше похоже на магазин).

### P1-3. Карточка курса почти пустая и с багом

**Где:** `templates/shop/single_course.html`.
**Факты:** `{{ course.students_qty }}` — опечатка, поля `students_qty` не существует (правильно `student_qty`),
поэтому на странице пустой `<p></p>`; нет описания, изображения, программы, отзывов; кнопка «Buy» ничего не
делает; `<a type="button">` — невалидный атрибут; блок `content` переопределён вручную вместо `shop_content`.
**Решения:** **A (рекомендую)** — добавить в модель `description`, `image`, `level`, `duration`, `slug`;
переверстать карточку (hero-блок, описание, программа, цена, CTA); исправить опечатку и оставить
`{% block shop_content %}`. **B** — минимум: исправить опечатку и добавить `description` (1 поле). **C** —
отдельная модель `Lesson`/`Module` и страница программы курса (ближе к реальному образовательному продукту).

### P1-4. 404 и маршруты

**Где:** `shop/views.py:26-35`, `shop/urls.py:8`, отсутствует `templates/404.html`.
**Факты:** `Course.objects.get` в `try/except` вместо `get_object_or_404`; маршрут без слэша — `/shop/1/`
отдаёт **404** (при этом `/shop/` — со слэшем, непоследовательно); шаблон 404 лежит в `includes/`, хотя это
полноценная страница; для `DEBUG=False` нет глобальных `404.html`/`500.html` — пользователь увидит голый
текст Django.
**Решения:** **A (рекомендую)** — `get_object_or_404`, маршрут `"<int:course_id>/"`, перенести шаблон в
`templates/shop/course_not_found.html`, добавить `templates/404.html` и `templates/500.html`. **B** —
class-based `DetailView` с `get_object_or_404` и `template_name_suffix` (меньше кода). **C** — slug-URL
(`/shop/python-basics/`) для SEO и читаемости; потребует `slug` в модели и миграцию.

### P1-5. Магазина нет: «Buy» ничего не делает

**Где:** `templates/shop/courses.html:30`, `templates/shop/single_course.html:9`.
**Факты:** кнопки — `<button type="button">` без обработчика; нет корзины, заказа, оформления, истории покупок;
нет регистрации/входа для покупателей (только админка); нет модели «куплено/доступ к курсу».
**Решения:** **A (рекомендую для учебного проекта)** — `Cart` на сессии + `Order`/`OrderItem` + страница
оформления (без реальной оплаты) + «Мои покупки». **B** — упрощённо: кнопка «Купить» создаёт `Order` сразу
и ведёт на `/orders/<id>/success/` (2 модели, 1 день). **C** — добавить платёжную песочницу (Stripe Checkout
test mode / ЮKassa test) — это же станет «внешним API» проекта.

### P1-6. Внешнего API нет вообще

**Факты:** в зависимостях нет ни `requests`, ни `httpx`; в коде нет ни одного исходящего запроса. То, что
сейчас есть в `api/`, — это **свой** API для внешних клиентов, а не интеграция с внешним сервисом.
**Решения:** **A (рекомендую)** — потреблять внешний API и показать это в UI: курсы валют для цены
(`exchangerate.host`/ЦБ РФ XML), погода/цитата на главной, либо платежи в тестовом режиме. Обязательно:
таймауты, retry, кэш (`cache.get/set`, 5–60 мин), graceful fallback при недоступности, мок в тестах.
**B** — только «предоставлять» API (довести текущее до REST-контракта: DRF, OpenAPI, пагинация, фильтры).
**C** — оба направления: свой API + интеграция (лучшая демонстрация навыков, но дольше).

### P1-7. Визуал: дефолтный Bootstrap и 8.4 МБ вендорных файлов

**Факты:** `static/` — 8.4 МБ, 44 файла, из них 22 `.map`; подключены неминифицированные `bootstrap.css`
(274 КБ) и `bootstrap.bundle.js` (203 КБ); **нет ни одного своего CSS/JS-файла**, нет изображений, логотипа, favicon.
Страницы выглядят как учебный пример: тёмный navbar, светлый фон, синяя кнопка, таблица вместо карточек.
**Решения:** **A (рекомендую)** — оставить Bootstrap, но подключить только `bootstrap.min.css`/`bundle.min.js`,
удалить `.map`/RTL/`esm`/`grid`/`reboot`/`utilities` (экономия ~8 МБ), добавить `static/css/theme.css`
(палитра, шрифт, тени, радиусы, карточки, hero, hover), карточки курсов сеткой вместо таблицы, изображения-заглушки
(локальные SVG). **B** — готовый шаблон (Start Bootstrap / Creative) + адаптация под Django: быстро и «красиво»,
но меньше своей работы. **C** — Tailwind + `django-tailwind`/CDN: современнее, но нужен Node-тулчейн; для
учебного проекта усложняет запуск.

### P1-8. Локализация, плюрализация, смешанные языки

**Где:** `config/settings.py:108` (`LANGUAGE_CODE = "en-us"`), `templates/shop/courses.html:10,15-19`,
`templates/shop/single_course.html:9`.
**Факты:** сайт русский, админка — английская; заголовки таблицы `Title / Price / Students Quantity / Category / Action`
и кнопка `Buy` — на английском; «Всего 5 курса:» — неверная форма; `align="center"` устарел.
**Решения:** **A (рекомендую)** — `LANGUAGE_CODE = "ru-ru"`, `TIME_ZONE = "Europe/Kaliningrad"`, все строки
в шаблонах на русском, плюрализация через `ngettext`-фильтр или `pluralize`-хак/свой `russian_plural`,
`align` → `text-center`. **B** — полноценная i18n (`{% trans %}`, `.po`/`.mo`, переключатель языка). **C** —
оставить смешанный язык (быстро, но выглядит сыро).

### P1-9. Админка не настроена, нет демо-данных

**Где:** `shop/admin.py`, отсутствуют `fixtures/` и management-команды.
**Факты:** `admin.site.register` без `list_display`, поиска, фильтров, сортировки; нет способа быстро
наполнить сайт — при первом запуске каталог пуст («Курсов нет»), смотреть нечего.
**Решения:** **A (рекомендую)** — `CourseAdmin`/`CategoryAdmin` (`list_display`, `list_filter`, `search_fields`,
`list_editable`, `prepopulated_fields` для slug) + команда `python manage.py seed_demo`
(8–12 курсов, категории, картинки). **B** — фикстуры JSON + `loaddata`. **C** — `django-admin-interface`/
`django-jazzmin` для красивой админки (косметика, не приоритет).

---

## 4. P2 — средние проблемы

| ID | Проблема | Где | Решения |
|---|---|---|---|
| P2-1 | **Нет тестов.** `tests.py` пустые, `pytest-django` в dev-зависимостях, но нет `[tool.pytest.ini_options]`/`conftest.py` — `pytest` не запустится. | `shop/tests.py`, `api/tests.py`, `pyproject.toml` | **A (рек.)** pytest-django + `DJANGO_SETTINGS_MODULE` + 15–20 тестов (views, filters, API, 404, валидация) + `factory_boy`; **B** — `manage.py test` без pytest; **C** — + `coverage` с порогом 80 % в CI |
| P2-2 | **Нет CI и линт «красный».** `ruff` — 5 ошибок, 5 файлов не отформатированы; нет GitHub Actions. | весь проект | **A (рек.)** GitHub Actions: `ruff check`, `ruff format --check`, `djlint --lint`, `pytest`, `makemigrations --check`; **B** — только pre-commit-хуки локально; **C** — + Dependabot |
| P2-3 | **README пустой (0 байт).** Непонятно, как запустить, какие переменные окружения нужны, где API. | `README.md` | **A (рек.)** README: описание, стек, установка (`uv sync`, `migrate`, `seed_demo`, `runserver`), структура, API-эндпоинты, скриншоты; **B** — + `docs/` с API-справкой; **C** — + `CONTRIBUTING.md`/`LICENSE` |
| P2-4 | **Нет загрузки изображений.** `MEDIA_URL`/`MEDIA_ROOT` не заданы, `Pillow` не установлен — картинку курса физически некуда положить. | `config/settings.py` | **A (рек.)** `MEDIA_URL="/media/"`, `MEDIA_ROOT`, `+ static(settings.MEDIA_URL, ...)` в dev-`urls.py`, `ImageField`, `Pillow`; **B** — внешние URL картинок в `URLField` (проще, но зависимость от чужих сайтов); **C** — S3/Cloudinary (избыточно) |
| P2-5 | **`api/models.py` — не модели, а tastypie-ресурсы.** Смешение слоёв, пустые `views.py`/`admin.py`/`tests.py`, пустая папка `migrations` без моделей. | `api/` | **A (рек.)** переименовать в `api/resources.py` (или удалить при переходе на DRF), убрать пустые файлы; **B** — оставить, добавить комментарий; **C** — реструктурировать в `api/v1/…` |
| P2-6 | **Модели бедные.** Нет `verbose_name` (админка на английском), `created_at = default=timezone.now` вместо `auto_now_add`, `title` не уникален, нет `related_name`, `Meta.ordering`, индексов, `updated_at`. | `shop/models.py` | **A (рек.)** добавить `verbose_name`, `auto_now_add`, `updated_at`, `related_name="courses"`, `ordering`, `db_index` для поиска, `unique=True` для категорий (+ миграция); **B** — только `verbose_name` и `auto_now_add`; **C** — `slug` + `get_absolute_url()` |
| P2-7 | **Настройки «по умолчанию».** Нет `DEFAULT_AUTO_FIELD`, `LOGGING`, прод-статики (WhiteNoise/`collectstatic`), `MEDIA`, security-флагов; SQLite только для dev; `STATIC_URL = "static/"` без ведущего слэша (работает, но не по конвенции). | `config/settings.py` | **A (рек.)** env-настройки + `DEFAULT_AUTO_FIELD` + `LOGGING` + WhiteNoise; **B** — + PostgreSQL через `docker-compose`; **C** — + `django-debug-toolbar`/`silk` в dev |
| P2-8 | **Шаблоны: сломанное наследование.** `home/base.html` объявляет `{% block body_class %}`, которого нет в `base.html`; `single_course.html` переопределяет `content` вместо `shop_content`; `home/index.html` дважды задаёт `title`; 404-шаблон в `includes/`. | `templates/` | **A (рек.)** почистить блоки, добавить `{% block body_class %}` в `base.html` и `{% block meta %}`, вынести 404; **B** — перейти на компонентные include-ы (`_course_card.html`, `_pagination.html`); **C** — + `django-components`/`slippers` |
| P2-9 | **API без контракта.** Нет фильтров/сортировки/`fields`, нет `throttling`, CORS, схемы/документации, `always_return_data`; `created_at` отдаётся без таймзоны (`2026-11-12T12:08:51.004584`). | `api/models.py` | **A (рек.)** DRF + `django-filter` + `drf-spectacular` (`/api/docs/`) + `ScopedRateThrottle`; **B** — допилить tastypie (`filtering`, `ordering`, `fields`, `cache`); **C** — GraphQL (не для этого проекта) |
| P2-10 | **API-ключи негде взять.** `ApiKeyAuthentication` требует `ApiKey`, но ресурса/сигнала/инструкции нет — студент не может проверить POST/DELETE. | `api/auth.py` | **A (рек.)** при переходе на DRF — токены (`authtoken`) и `/api/auth/token/`; **B** — сигнал `post_save` на `User` → создать `ApiKey`, + раздел в README; **C** — оставить только чтение (тогда ключи не нужны) |
| P2-11 | **Нет доступности/SEO-базы.** Устаревший `align="center"`, `type` у `<a>`, нет `meta description`, OG-тегов, favicon, `alt` (картинок нет), таблица не адаптивна на телефоне (`table` без `.table-responsive`). | `templates/` | **A (рек.)** семантика + `text-center`, `.table-responsive` (или карточки), `meta description`/OG, favicon; **B** — + `sitemap.xml`/`robots.txt`; **C** — + Lighthouse-аудит |
| P2-12 | **`main.py` — мусорный файл.** `@dataclass class Test` с `arg2 = str` (это атрибут класса, а не аннотация), `print("Hello from test-django!")` — не относится к Django, путает новичка. | `main.py` | **A (рек.)** удалить; **B** — перенести в `scripts/` как песочницу; **C** — оставить, но починить `arg2: str = ""` |

---

## 5. P3 — мелкие недочёты

1. `ruff`: неиспользуемые импорты в `api/admin.py`, `api/views.py`, `api/tests.py`, `shop/tests.py`; длинная строка `config/settings.py:91`.
2. `ruff format` переформатирует 5 файлов (одинарные кавычки в `manage.py`, `apps.py`, `wsgi.py`/`asgi.py`).
3. `pyproject.toml:4` — `description = "Add your description here"`.
4. `pyproject.toml:2` — имя `django-course` не совпадает с брендом TRShop.
5. `.gitignore:1` — случайная строка `book.pdf`.
6. `.prettier*` настроены, но нет `package.json`/CI — форматирование JSON/CSS не воспроизводимо.
7. `config/urls.py:32` — `name="admin"` у `admin.site.urls` не используется; docstring стоит после импортов.
8. `templates/base.html:14,27,30` — двойные кавычки внутри двойных в `{% url "..." %}`; `djlint` их принимает, но стиль стоит унифицировать на одинарные.
9. `shop/apps.py:5`, `api/apps.py:5` — одинарные кавычки (ruff format → двойные).
10. Нет favicon (`static/img/favicon.ico`), логотипа, `og:image` — вкладка браузера и шаринг выглядят пусто.

---

## 6. Куда двигаться: целевая картина

**Минимальный жизнеспособный магазин (MVP), который закрывает задачу «учебный сайт-магазин с внешним API и красивым визуалом»:**

```text
Category 1──* Course 1──* Review
                 │
                 ├── image, description, level, duration, slug, price(Decimal)
                 │
Cart ──* CartItem ──* Course          Order 1──* OrderItem *──1 Course
  │ (session/user)                      │  status, total, created_at
  └─────────────────────────────────────┘  user (auth)
```

- **Каталог:** карточки с картинками, фильтр (категория, цена), поиск `icontains`, сортировка, пагинация.
- **Страница курса:** hero, описание, программа, отзывы, «Купить», похожие курсы.
- **Покупка:** корзина (сессия) → оформление → заказ → «Мои покупки» (доступ к материалам).
- **Пользователи:** регистрация/вход/выход, профиль, история заказов.
- **API:** REST на DRF (курсы, категории, заказы), OpenAPI-схема, пагинация, фильтры, права.
- **Внешний API:** курсы валют/платёжная песочница с кэшем, таймаутами, fallback и моками в тестах.
- **Визуал:** своя тема поверх Bootstrap (или готовый шаблон), изображения, адаптив, аккуратная типографика.
- **Инфраструктура:** env-настройки, README с быстрым стартом, 20+ тестов, GitHub Actions, демо-данные.

**План по итерациям**

| Итерация | Содержание | Оценка |
|---|---|---|
| **0. Стабилизация** | P0-1…P0-8 + P2-1/P2-2 (линт, тесты каркаса), README-минимум | 3–4 ч |
| **1. Каталог** | Decimal-цена, slug, описание/картинки, поиск/фильтры/пагинация, карточки и тема, админка, `seed_demo` | 1–2 дня |
| **2. Покупка** | корзина, заказы, регистрация/вход, «Мои покупки», страницы ошибок | 2–3 дня |
| **3. API и интеграция** | DRF + OpenAPI, права, внешний API (валюты или Stripe test) с кэшем и fallback, тесты, CI | 2–3 дня |

---

## 7. Быстрые патчи (можно применить сразу)

```python
# config/settings.py
import os

DEBUG = os.getenv("DJANGO_DEBUG", "1") == "1"
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "dev-only-insecure-key")
ALLOWED_HOSTS = [h for h in os.getenv("DJANGO_ALLOWED_HOSTS", "*").split(",") if h]
CSRF_TRUSTED_ORIGINS = [o for o in os.getenv("DJANGO_CSRF_TRUSTED_ORIGINS", "").split(",") if o]
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
LANGUAGE_CODE = "ru-ru"
TIME_ZONE = "Europe/Kaliningrad"
```

```python
# shop/views.py
from django.db.models import Q
from django.shortcuts import get_object_or_404


def index(request):
    courses = Course.objects.select_related("category").order_by("-created_at")
    title = request.GET.get("title", "").strip()
    category = request.GET.get("category", "")
    if title:
        courses = courses.filter(title__icontains=title)
    if category.isdigit():
        courses = courses.filter(category_id=int(category))
    return render(request, "shop/courses.html", {...})


def single_course(request, course_id):
    course = get_object_or_404(Course.objects.select_related("category"), pk=course_id)
    return render(request, "shop/single_course.html", {"course": course})
```

```python
# api/models.py — минимальный фикс (если остаёмся на tastypie)
class CourseResource(ModelResource):
    class Meta:
        queryset = Course.objects.select_related("category")
        resource_name = "courses"
        allowed_methods = ["get"]  # запись — через админку
        authorization = ReadOnlyAuthorization()
        always_return_data = True

    def dehydrate(self, bundle):
        bundle.data["category_id"] = bundle.obj.category_id
        return bundle
```

```html
<!-- templates/shop/single_course.html -->
{{ course.student_qty }}        <!-- вместо students_qty -->
<div class="text-center">...</div>  <!-- вместо align="center" -->
```

```bash
# обязательные команды после правок
python manage.py makemigrations shop
python manage.py migrate
ruff check --fix . && ruff format .
djlint --reformat --profile django templates
```

---

## 8. Что нужно решить вам

Чтобы не делать лишнего, нужно определиться с четырьмя вещами:

1. **Что значит «внешний API»** — сайт *потребляет* чужой сервис, *предоставляет* свой для внешних клиентов, или оба варианта.
2. **Объём следующего шага** — только критичные баги, MVP-магазин целиком или полный рефакторинг с DRF.
3. **Стек API** — Django 5.2 LTS + DRF (стабильно, полезно для учёбы) или остаться на tastypie/Django 6.1.
4. **Визуал** — своя тема на Bootstrap, готовый шаблон или Tailwind.

Ответы на эти вопросы — и я начну с итерации 0: закрою P0, приведу линт/тесты в зелёное состояние и обновлю README.
