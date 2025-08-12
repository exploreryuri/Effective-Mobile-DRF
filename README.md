# authsys — Собственная аутентификация (JWT) и авторизация (RBAC) на DRF + Postgres

Мини‑проект, показывающий:

- **Аутентификацию** на JWT (access/refresh) без сторонних библиотек,
- **Авторизацию** через RBAC c моделью прав `resource:action:scope` и поддержкой `scope=ALL|OWN`,
- Разницу **401 (не аутентифицирован)** vs **403 (нет прав)** на живых мок‑ручках,
- **Админ‑API** для управления ролями/правами.

---

## Стек и ключевые решения

- **Django 4+**, **Django REST Framework**, **PostgreSQL**, **PyJWT**, **python‑dotenv**.
- Кастомный `User` (email — логин), soft‑delete через `is_active=False` + `deleted_at`.
- Свой `JWTAuthentication` (Bearer), **access** короткий (15 мин), **refresh** длинный (7 дней) с ревокацией/ротацией.
- RBAC: таблицы `roles`, `permissions(resource, action, scope)`, `role_permissions`, `user_roles`.
- Проверка `scope=OWN` в хендлере (сравнение `owner_id == request.user.id`).

---

## Быстрый старт

### 1) Установка

```bash
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
# или
pip install django djangorestframework psycopg2-binary PyJWT python-dotenv
```

### 2) Переменные окружения (`.env` в корне)

```
DJANGO_SECRET=
DB_NAME=authsys
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=127.0.0.1
DB_PORT=5432
```

### 3) Миграции и суперпользователь

```bash
python manage.py migrate
python manage.py createsuperuser --email admin@example.com
python manage.py runserver 0.0.0.0:8001
```

> При открытии API без токена ответы будут 401/403 в зависимости от пермишенов — это нормально.

---

## Структура проекта (минимально)

```
authsys/
├─ authsys/
│  ├─ settings.py
│  ├─ urls.py
├─ accounts/
│  ├─ models.py        # User, RefreshToken
│  ├─ views.py         # register/login/refresh/logout/me
│  ├─ serializers.py
│  ├─ jwt.py           # encode/decode токенов
│  └─ authentication.py# JWTAuthentication (Bearer)
├─ rbac/
│  ├─ models.py        # Role, Permission(scope), RolePermission, UserRole
│  ├─ views.py         # ViewSet’ы для RBAC управления
│  ├─ serializers.py
│  ├─ permissions.py   # require_permission(resource, action)
│  └─ auth_required.py # RequireAuthenticated401 → 401 без токена
└─ mockapp/
   └─ views.py         # /articles (моки для 401/403 и OWN)
```

---

## Настройки JWT (в `settings.py`)

```python
from datetime import timedelta
JWT_SECRET = SECRET_KEY
JWT_ALGORITHM = "HS256"
JWT_ACCESS_TTL = timedelta(minutes=15)
JWT_REFRESH_TTL = timedelta(days=7)

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": ["accounts.authentication.JWTAuthentication"],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
}
```

**Важно:** в `JWTAuthentication.authenticate_header()` возвращаем `"Bearer"`, чтобы DRF отдавал **401** без токена.

---

## Схема данных (упрощённо)

```
users(id, email*, password_hash, first_name, last_name, patronymic,
      is_active, is_staff, deleted_at, date_joined, ...)

refresh_tokens(id UUID, user_id->users, jti UUID, created_at, expires_at,
               revoked_at, user_agent, ip)

roles(id, name*, description)
permissions(id, resource, action, scope[ALL|OWN])
role_permissions(role_id->roles, permission_id->permissions)
user_roles(user_id->users, role_id->roles)
```

### Почему так

- **RBAC** прост и читаем для проверяющих.
- `scope=OWN` покрывает частый кейс «можно только своё».
- `refresh_tokens` в БД дают управляемый logout и отзыв.

---

## Маршруты (основные)

```
POST   /auth/register/        # публично (валидация пароля)
POST   /auth/login/           # публично → access+refresh
POST   /auth/refresh/         # публично (по refresh), ротация refresh
POST   /auth/logout/          # с access, ревокация всех активных refresh
GET    /users/me/             # с access
PATCH  /users/me/             # с access
DELETE /users/me/             # soft-delete (is_active=False + revoked refresh)
```

## Маршруты RBAC‑управления (для роли с правом `rbac:manage:ALL`)

```
GET/POST          /rbac/roles/
GET/PATCH/DELETE  /rbac/roles/{id}/
GET/POST          /rbac/permissions/
GET/PATCH/DELETE  /rbac/permissions/{id}/
GET/POST          /rbac/role-permissions/
GET/PATCH/DELETE  /rbac/role-permissions/{id}/
GET/POST          /rbac/user-roles/
GET/PATCH/DELETE  /rbac/user-roles/{id}/
```

## Mock‑объекты (демонстрация 401/403/OWN)

```
GET    /articles/             # требует право articles:read
PATCH  /articles/{id}/        # требует право articles:update (ALL или OWN)
```

`MOCK_ARTICLES = [{id:1, owner_id:2}, {id:2, owner_id:999}, {id:3, owner_id:42}]` — без БД.

- Без токена → **401**
- С токеном, но без права → **403**
- С `update:OWN` и чужим `owner_id` → **403**
- С `update:OWN` и своим `owner_id` → **200**

---

## RBAC: как читается право

Право — это **триада** `resource:action:scope`.

- Примеры: `articles:read:ALL`, `articles:update:OWN`, `rbac:manage:ALL`.
- Лучший `scope` определяется по ролям пользователя: если есть `ALL` — берём его; иначе если есть `OWN` — берём `OWN`; иначе — нет доступа.
- Для `OWN` конкретная проверка делается во вьюхе (сопоставление владельца).

### Минимальный набор тестовых прав/ролей

- Роли: `admin`, `editor`, `viewer`.
- Права:
  - `articles:read:ALL`
  - `articles:create:ALL`
  - `articles:update:OWN`
  - `rbac:manage:ALL` (только для `admin`)
- Привязки (пример):
  - `admin` → все выше
  - `editor` → `articles:read:ALL`, `articles:create:ALL`, `articles:update:OWN`
  - `viewer` → `articles:read:ALL`

---

## Потоки аутентификации

1. **Регистрация**: валидация пароля (DRF + Django validators), хэширование (`set_password`).
2. **Логин**: `authenticate(username=<email>, password=...)` → `access` + `refresh`. Записываем refresh в БД (с `jti`, `expires_at`, `user_agent`, `ip`).
3. **Refresh**: проверка подписи и \*\*нахождение refresh по \*\*`` → если активен, **ротируем** (старый `revoked_at=now`) и выдаём новую пару.
4. **Logout**: ревокация всех активных refresh‑токенов пользователя (глобальный выход).
5. **Soft‑delete**: `is_active=False`, `deleted_at=now`, ревокация refresh; дальнейший логин запрещён.

---

## Быстрые проверки (curl)

### Регистрация

```bash
curl -X POST http://127.0.0.1:8001/auth/register/ \
 -H "Content-Type: application/json" \
 -d '{"email":"user1@example.com","first_name":"User","last_name":"One","patronymic":"Test","password":"S0meStrongPass!","password2":"S0meStrongPass!"}'
```

### Логин → токены

```bash
curl -X POST http://127.0.0.1:8001/auth/login/ \
 -H "Content-Type: application/json" \
 -d '{"email":"user1@example.com","password":"S0meStrongPass!"}'
```

### Доступ к профилю

```bash
curl http://127.0.0.1:8001/users/me/ \
 -H "Authorization: Bearer ACCESS_TOKEN"
```

### 401 без токена

```bash
curl -i http://127.0.0.1:8001/articles/
```

### 200 с правом чтения

```bash
curl -i http://127.0.0.1:8001/articles/ \
 -H "Authorization: Bearer ACCESS_TOKEN"
```

### 403 на чужое при OWN

```bash
curl -i -X PATCH http://127.0.0.1:8001/articles/2/ \
 -H "Authorization: Bearer ACCESS_TOKEN" \
 -H "Content-Type: application/json" \
 -d '{"title":"X"}'
```

### 200 на своё при OWN

```bash
curl -i -X PATCH http://127.0.0.1:8001/articles/1/ \
 -H "Authorization: Bearer ACCESS_TOKEN" \
 -H "Content-Type: application/json" \
 -d '{"title":"My updated title"}'
```

### RBAC управление — только у admin (rbac\:manage\:ALL)

```bash
# список ролей
curl -i http://127.0.0.1:8001/rbac/roles/ \
 -H "Authorization: Bearer ADMIN_ACCESS"

# создать право
curl -i -X POST http://127.0.0.1:8001/rbac/permissions/ \
 -H "Authorization: Bearer ADMIN_ACCESS" \
 -H "Content-Type: application/json" \
 -d '{"resource":"articles","action":"delete","scope":"ALL"}'
```

---

## Частые ошибки и как починить

- **405 на /auth/register/** через GET\*\* → это POST‑ручка. Используйте POST в DRF UI или curl.
- **401 вместо 403 (или наоборот)** → убедитесь, что `JWTAuthentication.authenticate_header()` возвращает `"Bearer"`; а во вьюхах порядок пермишенов: сначала `RequireAuthenticated401`, затем `require_permission(...)`.
- **TOKEN\_INVALID при корректном токене** → в PyJWT иногда `sub` ожидается строкой. В этой реализации кладём `sub` как **строку**, а читаем `int(payload["sub"])`.
- **Токен валидный, но 401** → проверьте, не менялся ли `SECRET_KEY/JWT_SECRET`, не истёк ли `exp`, не обрезан ли токен (без `< >`).
- **Refresh не работает** → проверьте, что при логине создаётся запись в `refresh_tokens`, а при refresh старый помечается `revoked_at`.

---

## Почему «не из коробки»

- Свой JWT — видно, как формируется payload (`sub/typ/iat/exp`), что такое подпись, как и зачем ротировать refresh.
- Свой RBAC — нагляден принцип описания доступа к ресурсам в БД и проверка `OWN`.

## Куда развивать

- Хранить refresh в HttpOnly‑cookie, добавить fingerprint/one‑time rotation
- Rate limiting на login/refresh; защита от brute force и перечисления пользователей
- Email‑верификация и password reset
- Пагинация/фильтрация + пермишены на уровне queryset
- Audit‑логирование (кто и какие операции делал)

---
