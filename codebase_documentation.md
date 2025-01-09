# QuizMaker - Документация кодовой базы

## Структура проекта

```
QuizMaker/
├── UI/                      # Пользовательский интерфейс
│   ├── components/         # UI компоненты
│   │   ├── article_view.py # Компонент для отображения статьи
│   │   ├── quiz_list_view.py # Компонент для отображения списка тестов
│   │   └── quiz_view.py    # Компонент для отображения/редактирования теста
│   ├── services/          # Сервисы
│   │   └── quiz_service.py # Сервис для работы с тестами
│   ├── state/            # Управление состоянием
│   │   └── app_state.py  # Централизованное хранение состояния
│   ├── utils/            # Утилиты
│   │   └── async_utils.py # Утилиты для асинхронной работы
│   ├── article_service.py # Сервис для работы со статьями
│   ├── db_service.py     # Сервис для работы с базой данных
│   ├── quiz_ui.py        # UI для тестов
│   └── teacher_ui.py     # UI для учителя
├── ai_service.py         # Сервис для работы с AI (DeepSeek)
├── ai_service.log       # Лог AI сервиса
├── .env                # Конфигурационный файл
├── db_init.sql        # SQL для инициализации базы данных
├── requirements.txt   # Зависимости проекта
└── teacher_app.py     # Точка входа приложения
```

## Основные компоненты

### TeacherUI (teacher_ui.py)
Основной интерфейс учителя с двумя вкладками:
- "Create Quiz": Создание новых тестов
- "My Quizzes": Управление существующими тестами

Основные функции:
- Загрузка и обработка статей
- Генерация тестов с помощью AI
- Управление историей статей
- Настройка уровня сложности текста

### QuizService (services/quiz_service.py)
Сервис для работы с тестами:
- `generate_quiz()`: Генерация теста
- `regenerate_question()`: Регенерация отдельного вопроса
- `save_quiz()`: Сохранение теста

### AIService (ai_service.py)
Сервис для работы с DeepSeek AI:
- `clean_article()`: Очистка и форматирование текста статьи
- `adapt_text_level()`: Адаптация текста под уровень сложности
- `generate_quiz()`: Генерация вопросов для теста

### DBService (db_service.py)
Сервис для работы с Supabase:
- `save_test()`: Сохранение теста с генерацией кода доступа
- `save_article()`: Сохранение статьи с проверкой дубликатов
- `get_article_history()`: Получение истории статей
- `load_teacher_tests()`: Загрузка тестов учителя

## База данных (Supabase)

### Таблицы:
- `tests`: Тесты
  - id (UUID)
  - title (TEXT)
  - article_url (TEXT)
  - article_text (TEXT)
  - language_level (ENUM)
  - created_at (TIMESTAMP)
  - teacher_id (TEXT)

- `questions`: Вопросы
  - id (UUID)
  - test_id (UUID, FK)
  - question_text (TEXT)
  - correct_answer (TEXT)
  - options (JSONB)
  - order_number (INTEGER)

- `submissions`: Ответы студентов
  - id (UUID)
  - test_id (UUID, FK)
  - student_name (TEXT)
  - answers (JSONB)
  - score (INTEGER)
  - submitted_at (TIMESTAMP)

## Управление состоянием

### AppState (state/app_state.py)
Централизованное хранение состояния через st.session_state:

#### ArticleState:
- content: Текст статьи
- url: URL статьи
- title: Заголовок
- language_level: Уровень сложности
- processed_content: Обработанный текст

#### QuizState:
- questions: Список вопросов
- current_question: Текущий вопрос
- is_generated: Статус генерации

## Асинхронная обработка

### AsyncUtils (utils/async_utils.py)
Утилиты для работы с асинхронным кодом:
- `async_handler`: Декоратор для асинхронных функций
- `get_event_loop`: Контекстный менеджер для event loop

## Конфигурация

### Переменные окружения (.env):
- DEEPSEEK_API_KEY: Ключ API DeepSeek
- DEEPSEEK_API_BASE: URL API DeepSeek
- DEEPSEEK_API_MODEL: Модель DeepSeek
- SUPABASE_URL: URL Supabase
- SUPABASE_KEY: Ключ API Supabase

## Зависимости (requirements.txt)
- streamlit==1.29.0: Web-фреймворк
- supabase==2.3.0: Клиент Supabase
- requests==2.31.0: HTTP-клиент
- beautifulsoup4==4.12.2: Парсинг HTML
- openai==0.28.1: Клиент OpenAI/DeepSeek
- python-dotenv==1.0.0: Загрузка .env
- httpx==0.24.1: HTTP-клиент для асинхронных запросов

## Логирование
- Настроено через стандартный модуль logging
- Логи AI сервиса в ai_service.log
- Уровень логирования: INFO
- Формат: timestamp - level - message
