## Сервис для создания коротких ссылок
### Возможности
- Создание коротких ссылок (с кастомным alias или автоматически)
- Указание времени жизни ссылки (автоматическое удаление)
- Статистика переходов (количество, дата последнего использования)
- Поиск ссылок по оригинальному URL
- Удаление и обновление ссылок
- Группировка ссылок по проектам
- Кэширование популярных ссылок в Redis
- Фоновые задачи для очистки устаревших ссылок

### Технологии
- FastAPI — веб-фреймворк
- PostgreSQL — основная база данных
- Redis — кэширование
- SQLAlchemy — ORM
- APScheduler — фоновые задачи


### Установка и запуск
#### Локальный запуск
Клонировать репозиторий:

bash
git clone <url-репозитория>
cd url_shortener


Установить зависимости:

bash
pip install -r requirements.txt
Запустить PostgreSQL и Redis (через Docker):

bash
docker run -d --name postgres -e POSTGRES_USER=user -e POSTGRES_PASSWORD=pass -e POSTGRES_DB=urlshortener -p 5432:5432 postgres:15
docker run -d --name redis -p 6379:6379 redis

Запустить приложение:

bash
uvicorn src.main:app --reload

#### Запуск через Docker Compose
bash
docker-compose up --build

Приложение будет доступно по адресу: http://localhost:8000
Документация Swagger: http://localhost:8000/docs

### API Endpoints
1. Создание короткой ссылки
http
POST /links/shorten
Параметры запроса:

json
{
  "original_url": "string",
  "custom_url": "string",                     // опционально, кастомный alias
  "expires_at": "2026-03-09T16:56:51.556Z",  // опционально, время жизни
  "project": "string"                       // опционально, группировка по проектам
}


Пример запроса:

bash
curl -X 'POST' \
  'http://localhost:8000/links/shorten' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "original_url": "MY_LINK",
  "custom_url": "",
  "expires_at": "",
  "project": "string"
}'
Ответ:

json
{
  "short_code": "v54i1O",
  "original_url": "MY_LINK",
  "expires_at": null,
  "project": "string"
}

2. Редирект по короткой ссылке
http
GET /links/{short_code}
Пример:

bash
curl "http://localhost:8000/links/v54i1O"
Ответ: редирект на оригинальный URL или JSON:

json
{
  "url": "MY_LINK"
}

3. Получение статистики
http
GET /links/{short_code}/stats
Пример:

bash
curl "http://localhost:8000/links/v54i1O/stats"
Ответ:

json
{
  "original_url": "MY_LINK",
  "created_at": "2026-03-09T16:56:25.121154",
  "clicks": 1,
  "last_used": "2026-03-09T16:57:40.158261",
  "expires_at": null
}

4. Обновление ссылки
http
PUT /links/{short_code}
Пример:

bash
curl -X 'PUT' \
  'http://localhost:8000/links/v54i1O' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "original_url": "MY_LINK_22"
}'
Ответ:

json
{
  "short_code": "v54i1O",
  "new_url": "MY_LINK_22"
}

5. Удаление ссылки
http
DELETE /links/{short_code}
Пример:

bash
curl -X 'DELETE' \
  'http://localhost:8000/links/v54i1O' \
  -H 'accept: */*'
Ответ: 204 Successful Response


6. Поиск по оригинальному URL
http
GET /links/search/force?original_url={url}
Пример:

bash
curl -X 'GET' \
  'http://localhost:8000/links/search/force?original_url=mmm' \
  -H 'accept: application/json'
Ответ:

json
{
  "short_code": "5bceb7",
  "original_url": "mmm",
  "clicks": 0,
  "project": "string",
  "method": "python_loop"
}
7. Удаление неиспользуемых ссылок
http
POST /links/cleanup-unused?days=30
Пример:

bash
curl -X POST "http://localhost:8000/links/cleanup-unused?days=30"
Ответ:

json
{
  "deactivated": 5
}

8. История истекших ссылок
http
GET /links/expired
Пример:

bash
curl "http://localhost:8000/links/expired"
Ответ:

json
[
  {
    "short_code": "oldlink",
    "original_url": "https://example.com",
    "expires_at": "2026-03-01T00:00:00",
    "last_used": "2026-02-28T15:30:00"
  }
]

9. Ссылки по проекту
http
GET /links/projects/{project}
Пример:

bash
curl "http://localhost:8000/links/projects/search"
Ответ:

json
[
  {
    "short_code": "goog",
    "original_url": "https://google.com",
    "clicks": 42,
    "created_at": "2026-03-09T15:30:00"
  }
]
### База данных
Модель Link
Поле	Тип	Описание
id	Integer	Первичный ключ
short_code	String	Уникальный код ссылки
original_url	String	Оригинальный длинный URL
created_at	DateTime	Дата создания
expires_at	DateTime	Дата истечения срока (null = бессрочно)
clicks	Integer	Количество переходов
last_used	DateTime	Дата последнего использования
is_active	Boolean	Активна ли ссылка
project	String	Название проекта для группировки

### Фоновые задачи
Сервис использует APScheduler для выполнения фоновых задач:

Очистка кэша неиспользуемых ссылок — каждый день в 3:00

Обновление топа популярных ссылок — каждые 10 минут