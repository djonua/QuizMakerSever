import streamlit as st
from typing import Dict, List, Optional
from ..services.quiz_service import QuizService
from ..state.app_state import AppState
from ..utils.async_utils import async_handler

class QuizView:
    """Component for displaying a quiz"""
    
    def __init__(self, quiz_service: QuizService, supabase=None):
        self.quiz_service = quiz_service
        self.supabase = supabase
    
    def show_question(self, question: Dict, index: int, prefix: str = ""):
        """Display a single question"""
        with st.container():
            # Create two columns: for question and button
            col1, col2 = st.columns([10, 1])
            
            with col1:
                # Combine number with question
                st.write(f"**{index + 1}. {question.get('question')}**")
                
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
                        'question': q.get('question_text', 'No question'),
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
        article = st.session_state.article
        quiz = st.session_state.quiz
        
        if not article.content:
            st.error("No text available for regeneration")
            return
            
        try:
            new_question = await self.quiz_service.regenerate_question(
                article.content,
                index,
                quiz.questions,
                article.language_level
            )
            if new_question:
                quiz.questions[index] = new_question
                st.success("Question regenerated successfully!")
        except Exception as e:
            st.error(f"Failed to regenerate question: {str(e)}")
    
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
