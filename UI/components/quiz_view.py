import streamlit as st
from typing import Dict, List, Optional
from ..services.quiz_service import QuizService
from ..state.app_state import AppState
from ..utils.async_utils import async_handler
import logging

logger = logging.getLogger(__name__)

class QuizView:
    """Component for displaying a quiz"""
    
    def __init__(self, quiz_service: QuizService, supabase=None):
        self.quiz_service = quiz_service
        self.supabase = supabase
        logger.info(f"QuizView initialized with quiz_service: {quiz_service}")
    
    def show_question(self, question: Dict, index: int, prefix: str = ""):
        """Display a single question"""
        with st.container():
            # Create two columns: for question and button
            col1, col2 = st.columns([10, 1])
            
            with col1:
                # Combine number with question
                question_text = question.get('question_text') or question.get('question')
                st.write(f"**{index + 1}. {question_text}**")
                
                # Display answer options
                options = question.get("options", [])
                correct_answer = question.get("correct_answer")
                
                # If options are in JSON string format, convert to list
                if isinstance(options, str):
                    try:
                        import json
                        options = json.loads(options)
                    except:
                        options = []
                
                # Display answer options
                if isinstance(options, list):
                    for option in options:
                        if option == correct_answer:
                            st.markdown(f"☑ {option}")
                        else:
                            st.markdown(f"☐ {option}")
                
                # Add an empty line after the question block
                st.write("")
            
            with col2:
                if st.session_state.edit_mode:
                    self._show_regenerate_button(index, prefix)
    
    def load_test(self, test_id: str) -> Dict:
        """Load a test from the database"""
        try:
            # First, load the main test data
            test_result = self.supabase.table("tests")\
                .select("*")\
                .eq("id", test_id)\
                .single()\
                .execute()
            
            if not test_result or not hasattr(test_result, 'data'):
                return None
            
            test_data = test_result.data
            
            # Load article data into session state
            AppState.update_article(
                content=test_data.get('article_text'),
                url=test_data.get('url'),
                level=test_data.get('language_level'),
                title=test_data.get('title')
            )
            
            # Then load the questions for this test
            questions_result = self.supabase.table("questions")\
                .select("*")\
                .eq("test_id", test_id)\
                .order("order_number")\
                .execute()
            
            if questions_result and hasattr(questions_result, 'data'):
                # Convert questions to the required format
                formatted_questions = []
                for q in questions_result.data:
                    formatted_question = {
                        'question_text': q.get('question_text', 'No question'),
                        'correct_answer': q.get('correct_answer', ''),
                        'options': q.get('options', [])
                    }
                    formatted_questions.append(formatted_question)
                
                # Update quiz state with loaded questions
                AppState.update_quiz(formatted_questions)
                test_data['questions'] = formatted_questions
            
            return test_data
            
        except Exception as e:
            st.error(f"Failed to load test: {str(e)}")
            return None

    @async_handler
    async def _regenerate_question(self, index: int):
        """Regenerate a single question"""
        try:
            logger.info(f"Starting regeneration for question {index}")
            # Если это существующий тест, загружаем его заново для получения текста статьи
            if st.session_state.selected_test:
                logger.info(f"Loading test {st.session_state.selected_test}")
                test_data = self.load_test(st.session_state.selected_test)
                if not test_data:
                    st.error("Не удалось загрузить тест")
                    return
                article_text = test_data.get('article_text')
                logger.info(f"Got article text, length: {len(article_text) if article_text else 0}")
            else:
                article_text = st.session_state.article.content
                logger.info("Using article text from session state")
            
            if not article_text:
                st.error("Нет текста для регенерации вопроса")
                return
            
            logger.info("Calling quiz_service.regenerate_question")
            with st.spinner("Регенерация вопроса..."):
                new_question = await self.quiz_service.regenerate_question(
                    article_text,
                    index,
                    st.session_state.quiz.questions,
                    st.session_state.article.language_level
                )
                logger.info(f"Got new question: {new_question}")
                if new_question:
                    # Обновляем вопрос в state
                    st.session_state.quiz.questions[index] = {
                        "question_text": new_question["question"],
                        "options": new_question["options"],
                        "correct_answer": new_question["correct_answer"]
                    }
                    # Если есть test_id, обновляем вопрос в базе данных
                    if st.session_state.selected_test:
                        try:
                            # Получаем id вопроса из базы данных
                            questions_result = self.supabase.table("questions")\
                                .select("id")\
                                .eq("test_id", st.session_state.selected_test)\
                                .order("order_number")\
                                .execute()
                            
                            if questions_result and questions_result.data:
                                question_id = questions_result.data[index]["id"]
                                # Обновляем вопрос в базе данных
                                self.supabase.table("questions")\
                                    .update({
                                        "question_text": new_question["question"],
                                        "options": json.dumps(new_question["options"]),
                                        "correct_answer": new_question["correct_answer"]
                                    })\
                                    .eq("id", question_id)\
                                    .execute()
                        except Exception as e:
                            st.error(f"Ошибка при обновлении вопроса в базе данных: {str(e)}")
                            return
                    
                    st.success("Вопрос успешно обновлен!")
                    st.experimental_rerun()
        except Exception as e:
            st.error(f"Ошибка при регенерации вопроса: {str(e)}")
    
    def _show_regenerate_button(self, index: int, prefix: str):
        """Display the regenerate button"""
        # Add test_id and random suffix to button key to make it unique
        test_id = st.session_state.selected_test if st.session_state.selected_test else "new"
        import random
        import string
        suffix = ''.join(random.choices(string.ascii_lowercase, k=8))
        button_key = f"{prefix}regenerate_{test_id}_{index}_{suffix}"
        
        if st.button("🔄", key=button_key, 
                    help="Regenerate this question"):
            logger.info(f"Regenerate button clicked for question {index}")
            if not self.quiz_service:
                logger.error("quiz_service is None!")
                st.error("Quiz service not initialized!")
                return
            self._regenerate_question(index)
    
    @async_handler
    async def _save_quiz(self):
        """Save the quiz"""
        if not self.supabase:
            st.error("Database connection not available")
            return
            
        article = st.session_state.article
        # Get title from article or use first 30 chars of content
        title = None
        if article.title and article.title.strip():
            title = article.title
        
        await self.quiz_service.save_quiz(self.supabase, title)
    
    def show_quiz(self, prefix: str = ""):
        """Display the entire quiz"""
        # If this is a new test
        if hasattr(st.session_state, 'quiz') and st.session_state.quiz.questions:
            questions = st.session_state.quiz.questions
        # If this is an existing test
        elif st.session_state.selected_test:
            test = self.load_test(st.session_state.selected_test)
            if not test:
                st.error("Failed to load test")
                return
            questions = test.get('questions', [])
            st.title(test.get('title', 'Untitled Quiz'))
            # Update quiz state with loaded questions only in edit mode
            if st.session_state.edit_mode:
                AppState.update_quiz(questions)
        else:
            return
            
        with st.expander("Quiz", expanded=True):
            st.write("### Quiz Questions")
            for i, question in enumerate(questions):
                self.show_question(question, i, prefix)
            
            # Показываем кнопку Save Quiz для новых тестов или когда тест был сгенерирован
            if st.session_state.quiz.is_generated and not st.session_state.selected_test:
                st.markdown("---")
                if st.button("Save Quiz", 
                            key="save_quiz_btn",
                            use_container_width=True):
                    self._save_quiz()
