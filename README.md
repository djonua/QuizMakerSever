# QuizMaker - Интерактивная система для создания и проведения тестов

## Описание
QuizMaker - это система, позволяющая преподавателям создавать интерактивные тесты на основе статей из интернета. Система использует искусственный интеллект (DeepSeek) для обработки текста и генерации вопросов.

## Установка и настройка

### Требования
- Python 3.10 или выше
- Git
- Доступ к Supabase
- Доступ к DeepSeek API

### Шаги установки

1. Клонируйте репозиторий:
```bash
git clone https://github.com/djonua/QuizMakerSever.git
cd QuizMaker
```

2. Создайте виртуальное окружение и активируйте его:
```bash
python -m venv venv
.\venv\Scripts\activate  # для Windows
```

3. Установите зависимости:
```bash
pip install -r requirements.txt
```

4. Настройте переменные окружения:
   - Скопируйте файл `.env.example` в `.env`
   ```bash
   copy .env.example .env  # для Windows
   ```
   - Откройте `.env` в текстовом редакторе
   - Замените примеры значений на свои реальные ключи:
     - `DEEPSEEK_API_KEY`: Ваш ключ API DeepSeek
     - `DEEPSEEK_API_BASE`: URL API DeepSeek
     - `DEEPSEEK_API_MODEL`: Модель DeepSeek для генерации
     - `SUPABASE_URL`: URL вашего проекта Supabase
     - `SUPABASE_KEY`: Анонимный ключ Supabase
     - Опциональные настройки:
       - `LOG_LEVEL`: Уровень логирования (по умолчанию INFO)
       - `DEFAULT_LANGUAGE_LEVEL`: Уровень языка по умолчанию (B2)
       - `QUESTIONS_PER_TEST`: Количество вопросов в тесте (5)

5. Инициализируйте базу данных в Supabase:
   - Создайте новый проект в Supabase
   - Выполните SQL-скрипт из файла `db_init.sql`

### Запуск приложения

1. Активируйте виртуальное окружение (если еще не активировано):
```bash
.\venv\Scripts\activate  # для Windows
```

2. Запустите приложение:
```bash
python teacher_app.py
```

## Функциональность для преподавателя

### Работа с текстом
1. Ввод URL статьи для импорта
2. Автоматическая очистка текста от лишнего контента с помощью ИИ
3. Адаптация сложности текста:
   - Выбор уровня: A1, A2, B1, B2, C1, C2
   - Режим "Без изменений" - только очистка текста
   
### Создание тестов
1. Автоматическая генерация вопросов на основе текста
2. Настройка количества вопросов (1-20)
3. Возможность просмотра и редактирования сгенерированного теста
4. Отправка теста ученикам через Supabase

### История и управление
- Сохранение истории обработанных статей
- Просмотр всех созданных тестов
- Возможность редактирования и удаления тестов
- Фильтрация тестов по уровню сложности

## Технические особенности
- Streamlit для пользовательского интерфейса
- DeepSeek AI для обработки текста и генерации вопросов
- Supabase для хранения тестов и результатов
- Асинхронная обработка запросов к AI
- Пагинация для эффективной работы со списком тестов

## Логирование
- Все операции логируются в консоль
- Операции AI сервиса дополнительно логируются в `ai_service.log`
- Уровень логирования: INFO

## Зависимости
Основные:
- streamlit==1.29.0: Web-интерфейс приложения
- supabase==2.3.0: Взаимодействие с базой данных
- openai==0.28.1: Интеграция с DeepSeek AI
- python-dotenv==1.0.0: Управление переменными окружения

Вспомогательные:
- requests==2.31.0: Загрузка статей по URL
- beautifulsoup4==4.12.2: Парсинг HTML-контента
- httpx==0.24.1: Асинхронные HTTP-запросы (требуется для Supabase)

Все зависимости можно установить одной командой:
```bash
pip install -r requirements.txt
```

## Поддержка
При возникновении проблем:
1. Проверьте логи в консоли и `ai_service.log`
2. Убедитесь, что все переменные окружения установлены корректно
3. Проверьте подключение к DeepSeek и Supabase
4. Создайте issue в репозитории с описанием проблемы
