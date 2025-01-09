from dataclasses import dataclass
from typing import Optional, List, Dict
import streamlit as st
from datetime import datetime

@dataclass
class ArticleState:
    content: Optional[str] = None
    url: Optional[str] = None
    title: Optional[str] = None
    language_level: Optional[str] = None
    processed_content: Optional[str] = None

@dataclass
class QuizState:
    questions: List[Dict] = None
    current_question: int = 0
    is_generated: bool = False

class AppState:
    """Централизованное управление состоянием приложения"""
    
    @staticmethod
    def init_session_state():
        """Инициализация начального состояния"""
        if 'article' not in st.session_state:
            st.session_state.article = ArticleState()
        if 'quiz' not in st.session_state:
            st.session_state.quiz = QuizState()
        if 'show_article' not in st.session_state:
            st.session_state.show_article = False
        if 'article_expanded' not in st.session_state:
            st.session_state.article_expanded = True
        if 'selected_test' not in st.session_state:
            st.session_state.selected_test = None
        if 'edit_mode' not in st.session_state:
            st.session_state.edit_mode = False
        if 'current_page' not in st.session_state:
            st.session_state.current_page = 0
    
    @staticmethod
    def update_article(content: str, url: str, level: str, title: str = None):
        """Обновление состояния статьи"""
        st.session_state.article.content = content
        st.session_state.article.url = url
        st.session_state.article.language_level = level
        st.session_state.article.title = title
    
    @staticmethod
    def update_quiz(questions: List[Dict]):
        """Обновление состояния викторины"""
        st.session_state.quiz.questions = questions
        st.session_state.quiz.is_generated = True
    
    @staticmethod
    def clear_state():
        """Очистка состояния"""
        st.session_state.article = ArticleState()
        st.session_state.quiz = QuizState()
        # Сбрасываем дополнительные состояния
        st.session_state.show_article = False
        st.session_state.article_expanded = True  # Возвращаем к начальному состоянию
        if 'generate_quiz_btn' in st.session_state:
            del st.session_state.generate_quiz_btn
        if 'save_quiz_btn' in st.session_state:
            del st.session_state.save_quiz_btn
