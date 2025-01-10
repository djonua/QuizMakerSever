import streamlit as st
from supabase import create_client
import os
from dotenv import load_dotenv
import json
from datetime import datetime
import logging

# Initialize logger
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize Supabase client
supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

def load_test(access_code: str):
    """Load test from database using access code"""
    try:
        # Приводим код к верхнему регистру и убираем пробелы
        access_code = access_code.strip().upper()
        
        # Load test data
        logger.info(f"Trying to load test with access code: {access_code}")
        
        # Сначала проверяем существование теста
        test_query = supabase.table("tests")\
            .select("*")\
            .eq("access_code", access_code)
        
        test_result = test_query.execute()
        logger.info(f"Test query result: {test_result}")
        
        if not test_result.data:
            logger.warning(f"No test found with access code: {access_code}")
            return None
            
        test_data = test_result.data[0]  # Берем первый результат
        
        # Load questions
        logger.info(f"Loading questions for test_id: {test_data['id']}")
        questions = supabase.table("questions")\
            .select("*")\
            .eq("test_id", test_data["id"])\
            .order("order_number")\
            .execute()
            
        question_count = len(questions.data)
        logger.info(f"Found {question_count} questions")
        
        if question_count == 0:
            logger.warning(f"No questions found for test_id: {test_data['id']}")
            return None
            
        test_data["questions"] = questions.data
        return test_data
        
    except Exception as e:
        # Логируем ошибку, но пользователю показываем общее сообщение
        logger.error(f"Error loading test: {str(e)}", exc_info=True)
        return None

def save_submission(test_data: dict, student_name: str, answers: dict, score: int, detailed_answers: dict):
    """Save test submission with detailed answers"""
    try:
        submission = {
            "test_id": test_data["id"],
            "student_name": student_name,
            "answers": answers,  # Оригинальные ответы для обратной совместимости
            "detailed_answers": detailed_answers,  # Детальная информация по каждому ответу
            "score": score,
            "total_questions": len(test_data["questions"]),
            "percentage": round((score / len(test_data["questions"])) * 100, 1),
            "submitted_at": datetime.utcnow().isoformat()
        }
        result = supabase.table("submissions").insert(submission).execute()
        return result.data
    except Exception as e:
        logger.error(f"Error saving submission: {str(e)}")
        st.error(f"Error saving submission: {str(e)}")
        return None

def calculate_score(test_data: dict, answers: dict) -> tuple[int, dict]:
    """Calculate test score and prepare detailed answers"""
    correct_count = 0
    detailed_answers = {}
    
    for question in test_data["questions"]:
        q_id = str(question["id"])
        if q_id in answers:
            is_correct = answers[q_id] == question["correct_answer"]
            if is_correct:
                correct_count += 1
                
            detailed_answers[q_id] = {
                "question_text": question["question_text"],
                "student_answer": answers[q_id],
                "correct_answer": question["correct_answer"],
                "is_correct": is_correct,
                "order_number": question["order_number"]
            }
            
    return correct_count, detailed_answers

def main():
    st.set_page_config(
        page_title="QuizMaker - Student Interface",
        page_icon="📝",
        layout="wide"
    )
    
    # Добавляем CSS для анимированного фона
    st.markdown("""
        <style>
        .stApp {
            background: linear-gradient(-45deg, #ee7752, #e73c7e, #23a6d5, #23d5ab);
            background-size: 400% 400%;
            animation: gradient 15s ease infinite;
        }
        
        @keyframes gradient {
            0% {
                background-position: 0% 50%;
            }
            50% {
                background-position: 100% 50%;
            }
            100% {
                background-position: 0% 50%;
            }
        }
        
        div[data-testid="stForm"] {
            background-color: rgba(255, 255, 255, 0.95);
            padding: 2rem;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        
        div.stButton > button {
            width: 100%;
            background-color: #23a6d5;
            color: white;
            border: none;
            padding: 0.5rem 1rem;
            border-radius: 5px;
            transition: all 0.3s ease;
        }
        
        div.stButton > button:hover {
            background-color: #1b8ab0;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Центрируем заголовок
    st.markdown("<h1 style='text-align: center; color: white;'>QuizMaker - Student Test</h1>", unsafe_allow_html=True)
    
    # Initialize session state
    if "test_loaded" not in st.session_state:
        st.session_state.test_loaded = False
    if "test_data" not in st.session_state:
        st.session_state.test_data = None
    if "current_answers" not in st.session_state:
        st.session_state.current_answers = {}
    if "show_restart" not in st.session_state:
        st.session_state.show_restart = False
    if "error_message" not in st.session_state:
        st.session_state.error_message = None
    
    # Если тест не загружен, показываем форму авторизации по центру
    if not st.session_state.test_loaded:
        col1, col2, col3 = st.columns([1,2,1])
        with col2:
            # Test access code and student name input
            with st.form("test_form"):
                st.markdown("<h3 style='text-align: center;'>Вход в систему</h3>", unsafe_allow_html=True)
                student_name = st.text_input("Ваше имя").strip()
                access_code = st.text_input("Код доступа к тесту").strip()
                submit_button = st.form_submit_button("Начать тест")
                
                if submit_button:
                    if not student_name:
                        st.error("⚠️ Пожалуйста, введите ваше имя")
                    elif len(student_name) < 3:
                        st.error("⚠️ Имя должно содержать не менее 3 символов")
                    elif not access_code:
                        st.error("⚠️ Пожалуйста, введите код доступа к тесту")
                    else:
                        with st.spinner("Загрузка теста..."):
                            test_data = load_test(access_code)
                            if test_data:
                                st.session_state.test_data = test_data
                                st.session_state.test_loaded = True
                                st.session_state.student_name = student_name
                                st.session_state.error_message = None
                                st.experimental_rerun()
                            else:
                                st.error("❌ Неверный код доступа. Пожалуйста, проверьте код и попробуйте снова.")
    
    # Show error message if exists
    if st.session_state.error_message:
        st.error(st.session_state.error_message)
    
    # Show test if loaded
    if st.session_state.test_loaded and st.session_state.test_data:
        # Добавляем белый фон для теста
        st.markdown("""
            <style>
            .stApp {
                background: white !important;
            }
            </style>
        """, unsafe_allow_html=True)
        
        test_data = st.session_state.test_data
        
        # Show test info
        st.header(test_data["title"])
        with st.expander("Информация о тесте", expanded=True):
            st.write(f"**Уровень сложности:** {test_data['language_level']}")
            st.write(f"**Количество вопросов:** {len(test_data['questions'])}")
            st.write(f"**Студент:** {st.session_state.student_name}")
        
        st.markdown("---")
        
        # Initialize test completion state if not exists
        if "test_completed" not in st.session_state:
            st.session_state.test_completed = False
        
        # Show questions only if test is not completed
        if not st.session_state.test_completed:
            with st.form("quiz_form"):
                for i, question in enumerate(test_data["questions"], 1):
                    q_id = str(question["id"])
                    st.subheader(f"Вопрос {i}")
                    st.write(f"**{question['question_text']}**")
                    options = question["options"]
                    if isinstance(options, str):
                        options = json.loads(options)
                    
                    # Radio buttons for answers
                    answer = st.radio(
                        "Выберите ответ:",
                        options=options,
                        key=f"q_{q_id}",
                        index=None  # Не выбирать ничего по умолчанию
                    )
                    st.session_state.current_answers[q_id] = answer
                    st.markdown("---")
                
                # Submit button
                if st.form_submit_button("Завершить тест"):
                    # Проверяем, все ли вопросы отвечены
                    unanswered = [i+1 for i, q in enumerate(test_data["questions"]) 
                                if st.session_state.current_answers.get(q["id"]) is None]
                    if unanswered:
                        st.error(f"Пожалуйста, ответьте на все вопросы. Не отвечены вопросы: {', '.join(map(str, unanswered))}")
                        return
                        
                    score, detailed_answers = calculate_score(test_data, st.session_state.current_answers)
                    total_questions = len(test_data["questions"])
                    
                    # Save submission
                    with st.spinner("Сохранение результатов..."):
                        save_submission(
                            test_data,
                            st.session_state.student_name,
                            st.session_state.current_answers,
                            score,
                            detailed_answers
                        )
                    
                    # Update session state
                    st.session_state.test_completed = True
                    st.session_state.test_score = score
                    st.session_state.total_questions = total_questions
                    st.session_state.detailed_answers = detailed_answers
                    st.experimental_rerun()
        
        # Show results if test is completed
        if st.session_state.test_completed:
            # Show results
            st.success("✅ Тест успешно завершен!")
            st.balloons()
            
            score = st.session_state.test_score
            total_questions = st.session_state.total_questions
            detailed_answers = st.session_state.detailed_answers
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Правильных ответов", f"{score}/{total_questions}")
            with col2:
                percentage = (score/total_questions)*100
                st.metric("Процент выполнения", f"{percentage:.1f}%")
            with col3:
                grade = "Отлично" if percentage >= 90 else "Хорошо" if percentage >= 75 else "Удовлетворительно" if percentage >= 60 else "Требует улучшения"
                st.metric("Оценка", grade)
            
            # Показываем детальный разбор ответов
            st.markdown("### Разбор ответов")
            for q_id, answer_info in detailed_answers.items():
                with st.expander(f"Вопрос {answer_info['order_number']}", expanded=False):
                    st.write(f"**Вопрос:** {answer_info['question_text']}")
                    st.write(f"**Ваш ответ:** {answer_info['student_answer']}")
                    if answer_info['is_correct']:
                        st.success("✅ Правильно!")
                    else:
                        st.error(f"❌ Неправильно. Правильный ответ: {answer_info['correct_answer']}")
            
            # Show restart button
            if st.button("Пройти другой тест"):
                # Reset all states
                st.session_state.test_loaded = False
                st.session_state.test_data = None
                st.session_state.current_answers = {}
                st.session_state.test_completed = False
                if "test_score" in st.session_state:
                    del st.session_state.test_score
                if "total_questions" in st.session_state:
                    del st.session_state.total_questions
                if "detailed_answers" in st.session_state:
                    del st.session_state.detailed_answers
                st.experimental_rerun()

if __name__ == "__main__":
    main()
