# Currency Exchange Service

Сервис обмена валют по официальным курсам НБ РБ. Python 3.12, FastAPI, PostgreSQL.

## Развёртывание

Нужен Docker.

```bash
docker compose up --build
```

Команда поднимает PostgreSQL и сервис. Сервис сам применяет миграции и загружает курсы при старте.

- Swagger: http://localhost:8000/docs
- Сброс данных: `docker compose down -v`

### Хранилище

PostgreSQL: сделки связаны с деньгами, поэтому нужны транзакции и точные десятичные числа.

Таблицы: `exchange_rates` (курсы НБ РБ по датам) и `deals` (сделки со статусом `PENDING`, `CONFIRMED`, `REJECTED`).

## API

Описание, примеры запросов и ответов: в Swagger (`/docs`).

| Метод | Путь | Описание |
|---|---|---|
| GET | `/v1/exchange/rates` | Курсы на сегодня |
| POST | `/v1/exchange/deals` | Расчёт обмена: сумма, исходная и целевая валюта. Возвращает сумму, курс и id сделки |
| POST | `/v1/exchange/{deal_id}/resolve` | Подтвердить или отклонить сделку: `confirm` / `reject` |
| GET | `/v1/exchange/pending` | Незавершённые сделки |
| GET | `/v1/exchange/report` | Отчёт за период: `date_from`, `date_to`, `currency` (необязательно) |

Отчёт возвращает по каждой валюте: сумму, пришедшую в кассу (`received`), сумму, ушедшую из кассы (`paid_out`),
и количество сделок (`deals_count`). Учитываются подтверждённые сделки по дате подтверждения (время Минска,
границы включительно).
