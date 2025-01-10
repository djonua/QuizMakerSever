# QuizMaker - Студенческий интерфейс

Это ученическая версия приложения [QuizMaker](https://github.com/djonua/QuizMakerSever).
Позволяет студентам проходить тесты, созданные преподавателями.

## Установка

1. Клонируйте репозиторий:
```bash
git clone https://github.com/djonua/QuizMakerSever.git
cd QuizMakerSever/student
```

2. Создайте виртуальное окружение:
```bash
python3 -m venv venv
source venv/bin/activate  # для Linux
```

3. Установите зависимости:
```bash
pip install -r ../requirements.txt
```

4. Скопируйте и настройте переменные окружения:
```bash
cp ../.env.example .env
# Отредактируйте .env, добавив ваши ключи Supabase
```

5. Запустите приложение:
```bash
streamlit run student_app.py --server.port 8502
```

Приложение будет доступно по адресу http://localhost:8502

> Примечание: Порт 8502 используется, чтобы не конфликтовать с учительской версией приложения, которая работает на порту 8501.

## Использование

1. Введите ваше имя
2. Введите код доступа к тесту (получите его у преподавателя)
3. Нажмите "Start Test"
4. Ответьте на все вопросы
5. Нажмите "Submit Test" для завершения

## База данных

База данных содержит следующие таблицы:

### Tests
-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create tests table
CREATE TABLE IF NOT EXISTS tests (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title TEXT NOT NULL,
    article_url TEXT NOT NULL,
    article_text TEXT NOT NULL,
    language_level TEXT CHECK (language_level IN ('A1', 'A2', 'B1', 'B2', 'C1', 'C2', 'original')) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    teacher_id TEXT NOT NULL,
    access_code TEXT UNIQUE NOT NULL
);

-- Create questions table
CREATE TABLE IF NOT EXISTS questions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    test_id UUID REFERENCES tests(id) ON DELETE CASCADE,
    question_text TEXT NOT NULL,
    correct_answer TEXT NOT NULL,
    options JSONB NOT NULL,
    order_number INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create submissions table
CREATE TABLE IF NOT EXISTS submissions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    test_id UUID REFERENCES tests(id) ON DELETE CASCADE,
    student_name TEXT NOT NULL,
    answers JSONB NOT NULL,
    detailed_answers JSONB,  -- Детальная информация о каждом ответе
    score INTEGER NOT NULL,
    total_questions INTEGER,  -- Общее количество вопросов
    percentage DECIMAL(5,2),  -- Процент правильных ответов
    submitted_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Структура detailed_answers:
{
    "question_id": {
        "question_text": "Текст вопроса",
        "student_answer": "Ответ студента",
        "correct_answer": "Правильный ответ",
        "is_correct": true/false,
        "order_number": 1
    },
    ...
}

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_questions_test_id ON questions(test_id);
CREATE INDEX IF NOT EXISTS idx_submissions_test_id ON submissions(test_id);
CREATE INDEX IF NOT EXISTS idx_tests_created_at ON tests(created_at);
CREATE INDEX IF NOT EXISTS idx_submissions_submitted_at ON submissions(submitted_at);
CREATE INDEX IF NOT EXISTS idx_tests_access_code ON tests(access_code);
