# Деплой на Oracle Cloud (бесплатно навсегда)

Oracle Cloud предоставляет бесплатный VPS навсегда (Always Free):
- 2 ядра ARM, 12 GB RAM — более чем достаточно для бота
- Никаких кредитов, не истекает

---

## Шаг 1 — Создать аккаунт Oracle Cloud

1. Зайди на cloud.oracle.com
2. Нажми **«Start for free»**
3. Заполни данные — потребуется **карта** (для верификации, деньги не снимаются)
4. Выбери регион ближайший к тебе (потом не изменить!)
5. Дождись активации аккаунта (может занять до 24 часов)

---

## Шаг 2 — Создать виртуальную машину

1. В консоли Oracle Cloud открой **«Compute»** → **«Instances»** → **«Create Instance»**

2. Настройки:
   - **Name**: kwork-bot (любое)
   - **Image**: Ubuntu 22.04
   - **Shape**: нажми «Change Shape» → выбери **«Ampere»** (ARM) → **VM.Standard.A1.Flex**
   - **OCPUs**: 1, **Memory**: 6 GB (в рамках бесплатного лимита)

3. **SSH ключи**: нажми «Generate a key pair» и скачай оба файла (`*.key` и `*.pub`)  
   Сохрани приватный ключ — он нужен для входа на сервер.

4. Нажми **«Create»**

5. Дождись статуса **«Running»** (1–3 минуты)

---

## Шаг 3 — Открыть порты (Security Rules)

По умолчанию Oracle блокирует все входящие соединения, кроме SSH.  
Боту это не нужно (он сам инициирует соединения), можно пропустить.

---

## Шаг 4 — Подключиться к серверу

Скопируй **Public IP** из карточки инстанса, затем подключись:

**На Linux/Mac:**
```bash
chmod 400 ~/Downloads/твой-ключ.key
ssh -i ~/Downloads/твой-ключ.key ubuntu@<ПУБЛИЧНЫЙ_IP>
```

**На Windows** — используй PuTTY или Windows Terminal:
```
ssh -i C:\Users\ТЫ\Downloads\твой-ключ.key ubuntu@<ПУБЛИЧНЫЙ_IP>
```

---

## Шаг 5 — Установить Docker

```bash
# Обновляем систему
sudo apt update && sudo apt upgrade -y

# Устанавливаем Docker
curl -fsSL https://get.docker.com | sudo sh

# Добавляем пользователя в группу docker (чтобы не писать sudo)
sudo usermod -aG docker ubuntu

# Перезайди на сервер чтобы применилось:
exit
# затем снова подключись по SSH
```

---

## Шаг 6 — Загрузить код на сервер

**Вариант А — через GitHub (рекомендуется):**
```bash
# На сервере:
git clone https://github.com/ТВОЙ_НИКНЕЙМ/НАЗВАНИЕ_РЕПО.git
cd НАЗВАНИЕ_РЕПО
```

**Вариант Б — скопировать файлы напрямую:**
```bash
# На своём компе:
scp -i ~/Downloads/твой-ключ.key -r /путь/к/parsing_kwork ubuntu@<IP>:~/kwork_bot
```

---

## Шаг 7 — Создать файл с переменными окружения

```bash
# На сервере, в папке с проектом:
nano .env
```

Вставь:
```
BOT_TOKEN=твой_токен_от_BotFather
CHAT_ID=твой_chat_id
CHECK_INTERVAL=3600
DB_PATH=/app/data/kwork_bot.db
```

Сохрани: `Ctrl+O`, `Enter`, `Ctrl+X`

---

## Шаг 8 — Создать папку для базы данных

```bash
mkdir -p ~/kwork_data
```

---

## Шаг 9 — Собрать и запустить Docker контейнер

```bash
# Собираем образ (займёт 3–7 минут, скачивает Playwright + Chromium)
docker build -t kwork-bot .

# Запускаем контейнер
docker run -d \
  --name kwork-bot \
  --restart unless-stopped \
  --env-file .env \
  -e DB_PATH=/data/kwork_bot.db \
  -v ~/kwork_data:/data \
  kwork-bot
```

Флаг `--restart unless-stopped` — контейнер будет автоматически перезапускаться после перезагрузки сервера.

---

## Шаг 10 — Проверить что всё работает

```bash
# Смотрим логи (Ctrl+C для выхода)
docker logs -f kwork-bot
```

Если всё хорошо, увидишь что-то вроде:
```
2024-01-01 12:00:00 - INFO - Starting scheduled check...
2024-01-01 12:00:05 - INFO - Found 20 orders on page. Processing...
```

---

## Полезные команды

```bash
# Остановить бота
docker stop kwork-bot

# Запустить снова
docker start kwork-bot

# Перезапустить
docker restart kwork-bot

# Посмотреть статус
docker ps

# Обновить бота (после изменений в коде)
git pull
docker build -t kwork-bot .
docker stop kwork-bot
docker rm kwork-bot
docker run -d --name kwork-bot --restart unless-stopped --env-file .env -e DB_PATH=/data/kwork_bot.db -v ~/kwork_data:/data kwork-bot
```

---

## Если нужно войти внутрь контейнера

```bash
docker exec -it kwork-bot bash
```

---

## Итог

После успешного запуска бот работает 24/7 полностью бесплатно.  
Oracle не отключает Always Free инстансы, если ты хотя бы иногда заходишь в консоль (раз в 6–12 месяцев).
