# Avito-merch-shop
Тестовое задание для стажёра Backend-направления (зимняя волна 2025)
## Описание
В Авито существует внутренний магазин мерча, где сотрудники могут приобретать товары за монеты (coin). Каждому новому сотруднику выделяется 1000 монет, которые можно использовать для покупки товаров. Кроме того, монеты можно передавать другим сотрудникам в знак благодарности или как подарок. Этот проект представляет из себя реализацию данного магазина мерча.
## Функционал
✅ Авторизация с помощью JWT

✅ Кэширование Redis

✅ Rate Limiter
## Используемый стэк
- Python 3.11.5
- FastAPI
- PostgreSQL
- Redis
- Alembic
- SQLAlchemy
- Docker
- Locust
- PyTest
## Инструкция по запуску
1. Клонируем репозиторий и переходим в целевую папку:

```
git clone https://github.com/valkievan/Avito-merch-shop/tree/main
cd Avito-merch-shop
```

2. Собираем и запускаем контейнер:

```
docker compose up --build
```
Миграции применяются автоматически во время запуска контейнера

*После запуска API будет доступен по адресу: http://localhost:8080*
## Тесты
Для тестирования используется фреймворк **Pytest**. Суммарное тестовое покрытие проекта составляет **77%**. Это также отражено в файле coverage.txt
### Запуск тестов
```
docker compose exec app pytest tests -v
```
Вывод

![image](https://github.com/user-attachments/assets/e2302e4e-db81-4438-8301-2e87970e3a1c)
### Запуск тестов с покрытием кода
```
docker compose exec app pytest --cov=app --cov-report=term-missing 
```
Вывод

![image](https://github.com/user-attachments/assets/14ea2b85-8e89-41e8-aa34-d90075ae8323)
