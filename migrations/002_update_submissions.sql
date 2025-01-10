-- Добавляем новые колонки в таблицу submissions
ALTER TABLE submissions
ADD COLUMN IF NOT EXISTS detailed_answers JSONB,
ADD COLUMN IF NOT EXISTS total_questions INTEGER,
ADD COLUMN IF NOT EXISTS percentage DECIMAL(5,2);

-- Создаем индекс для быстрого поиска по процентам
CREATE INDEX IF NOT EXISTS idx_submissions_percentage ON submissions(percentage);

-- Обновляем существующие записи (если они есть)
UPDATE submissions 
SET total_questions = (
    SELECT COUNT(*) 
    FROM questions 
    WHERE questions.test_id = submissions.test_id
),
percentage = (score::decimal / (
    SELECT COUNT(*) 
    FROM questions 
    WHERE questions.test_id = submissions.test_id
) * 100)
WHERE total_questions IS NULL;

-- Добавляем комментарии к колонкам
COMMENT ON COLUMN submissions.detailed_answers IS 'Детальная информация о каждом ответе студента в формате JSONB';
COMMENT ON COLUMN submissions.total_questions IS 'Общее количество вопросов в тесте';
COMMENT ON COLUMN submissions.percentage IS 'Процент правильных ответов';

-- Обновляем README с новой структурой
COMMENT ON TABLE submissions IS 'Таблица для хранения результатов тестирования студентов';
