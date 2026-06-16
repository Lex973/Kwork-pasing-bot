# Деплой на Railway

## Что нужно
- Аккаунт на railway.app (можно войти через GitHub)
- Аккаунт на GitHub (для загрузки кода)

---

## Шаг 1 — Загрузить код на GitHub

1. Создай репозиторий на github.com (кнопка «New repository»)
2. Инициализируй git и загрузи проект:

```bash
cd /путь/к/parsing_kwork
git init
git add .
git commit -m "init"
git remote add origin https://github.com/ТВОЙ_НИКНЕЙМ/НАЗВАНИЕ_РЕПО.git
git push -u origin main
```

> Убедись что файл `.env` НЕ попал в репозиторий. Добавь `.env` в `.gitignore`.

---

## Шаг 2 — Создать проект на Railway

1. Зайди на railway.app и нажми **«New Project»**
2. Выбери **«Deploy from GitHub repo»**
3. Выбери свой репозиторий
4. Railway автоматически найдёт `Dockerfile` и начнёт сборку

---

## Шаг 3 — Добавить переменные окружения

1. В проекте Railway открой вкладку **«Variables»**
2. Добавь переменные:

| Ключ | Значение |
|------|----------|
| `BOT_TOKEN` | токен от @BotFather |
| `CHAT_ID` | ID твоего чата/канала |
| `CHECK_INTERVAL` | `3600` (каждый час) |

> Как узнать CHAT_ID: напиши боту @userinfobot — он покажет твой ID.  
> Для канала: добавь @userinfobot в канал, он покажет ID канала.

---

## Шаг 4 — Деплой

После добавления переменных Railway автоматически перезапустит деплой.  
Смотри логи во вкладке **«Deployments»** → клик на текущий деплой → **«View Logs»**.

Если бот запустился — в логах увидишь:
```
INFO - Starting scheduled check...
```

---

## Важно про SQLite на Railway

Railway при каждом редеплое пересоздаёт контейнер, и база данных `kwork_bot.db` **сбрасывается**.  
Это значит бот при рестарте снова отправит все найденные заказы как новые.

**Решение** — подключить постоянное хранилище:
1. В проекте Railway нажми **«+ New»** → **«Volume»**
2. Укажи mount path: `/app/data`
3. В коде `database.py` замени путь к БД:

```python
# было:
class Database:
    def __init__(self, db_path="kwork_bot.db"):

# стало:
import os
class Database:
    def __init__(self, db_path=None):
        if db_path is None:
            db_path = os.environ.get("DB_PATH", "kwork_bot.db")
```

4. Добавь переменную `DB_PATH=/app/data/kwork_bot.db` в Variables на Railway

---

## Бесплатный лимит Railway

- $5 кредитов в месяц бесплатно
- Бот с Playwright потребляет ~0.5–1$/месяц при интервале проверки 1 час
- Т.е. **работает бесплатно** при умеренном использовании
