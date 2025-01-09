import streamlit as st
import logging
from .components.quiz_list_view import QuizListView
from .components.quiz_view import QuizView
from .services.quiz_service import QuizService
import pandas as pd
from typing import Dict, List
from supabase import Client

logger = logging.getLogger(__name__)

def show_tests_tab(supabase, ai_service=None):
    """Show teacher's tests tab"""
    try:
        # Инициализируем состояние, если его нет
        if 'selected_test' not in st.session_state:
            st.session_state.selected_test = None
            st.session_state.edit_mode = False

        # Если выбран тест для просмотра/редактирования
        if st.session_state.selected_test:
            # Кнопка возврата к списку
            if st.button("← Back to Tests"):
                st.session_state.selected_test = None
                st.session_state.edit_mode = False
                st.rerun()
            
            # Показываем выбранный тест
            quiz_service = QuizService(ai_service) if ai_service else None
            quiz_view = QuizView(quiz_service, supabase)
            quiz_view.show_quiz()
        else:
            # Показываем список тестов
            quiz_list = QuizListView(supabase)
            quiz_list.show_tests()
                                    
    except Exception as e:
        logger.error(f"Error loading tests: {str(e)}", exc_info=True)
        st.error(f"Failed to load tests: {str(e)}")
