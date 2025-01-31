import streamlit as st
import asyncio
import logging
import os
from typing import Dict, List
from .components.article_view import ArticleView
from .components.quiz_view import QuizView
from .components.results_view import show_results_tab
from .services.quiz_service import QuizService
from .state.app_state import AppState
from .utils.async_utils import async_handler
from supabase import create_client, Client
from dotenv import load_dotenv
from datetime import datetime
from .db_service import (
    save_test, save_article, get_article_history,
    get_article_by_id, load_teacher_tests, test_supabase_connection
)
from .article_service import extract_title, fetch_article
from .quiz_ui import show_tests_tab
from ai_service import AIService, test_ai_connection

__all__ = ['teacher_ui']

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def init_services():
    """Initialize AI service, Quiz service and Supabase client"""
    try:
        # Initialize AI service
        ai_service = AIService()
        logger.info("AI service initialized")
        
        # Initialize Quiz service
        quiz_service = QuizService(ai_service)
        logger.info("Quiz service initialized")
        
        # Initialize Supabase client
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")
        if not url or not key:
            raise ValueError("Supabase credentials not found in environment")
        supabase = create_client(url, key)
        logger.info("Supabase client initialized")
        
        return ai_service, quiz_service, supabase
    except Exception as e:
        logger.error(f"Failed to initialize services: {str(e)}", exc_info=True)
        raise

def teacher_ui():
    """Teacher UI for article processing and quiz generation"""
    try:
        # Configure page
        st.set_page_config(
            page_title="QuizMaker - Teacher Interface",
            page_icon="📚",
            layout="wide"
        )
        
        # Initialize services
        ai_service, quiz_service, supabase = init_services()
        
        # Initialize session state
        AppState.init_session_state()
        
        # Create tabs
        tab1, tab2, tab3 = st.tabs(["Create Quiz", "My Quizzes", "Results"])
        
        with tab1:
            st.title("Create Quiz")
            
            # Settings sidebar
            with st.sidebar:
                st.header("Settings")
                
                # Text difficulty level
                language_level = st.selectbox(
                    "Text Difficulty Level",
                    ["No changes", "A1", "A2", "B1", "B2", "C1", "C2"],
                    index=0
                )
                
                # Number of questions
                questions_count = st.slider(
                    "Number of Questions",
                    min_value=1,
                    max_value=20,
                    value=5
                )
                
                # Article history
                st.header("Article History")
                history = get_article_history(supabase)
                
                if history:
                    for article in history:
                        if st.button(article["title"], key=article["id"]):
                            article_data = get_article_by_id(supabase, article["id"])
                            if article_data:
                                st.session_state.article = article_data
                                st.experimental_rerun()
            
            # Main content area for article URL input and processing
            url = st.text_input("Enter article URL", key="article_url")
            if url and st.button("Process Article", key="process_btn"):
                process_article(ai_service, supabase, url, language_level)
                
            # Show article content if it exists
            if "article" in st.session_state:
                article = st.session_state.article
                article_view = ArticleView(
                    supabase=supabase,
                    on_generate_quiz=lambda: generate_quiz(ai_service, questions_count)
                )
                article_view.show_article(article)
                
                # Show quiz if generated
                if st.session_state.quiz.is_generated:
                    quiz_view = QuizView(quiz_service, supabase)
                    quiz_view.show_quiz()
        
        with tab2:
            show_tests_tab(supabase, ai_service)
            
        with tab3:
            show_results_tab(supabase)
            
    except Exception as e:
        logger.error("Error in teacher UI:", exc_info=True)
        st.error(f"Error in teacher UI: {str(e)}")

@async_handler
async def process_article(ai_service, supabase, url: str, language_level: str):
    """Processing the article"""
    try:
        with st.spinner("Loading and processing the article..."):
            html_content = fetch_article(url)
            if not html_content:
                st.error("Failed to load the article")
                return
            
            clean_text = await ai_service.clean_article(html_content)
            if not clean_text:
                st.error("Failed to extract article text")
                return
                
            if language_level != "No changes":
                with st.spinner(f"Adapting text to level {language_level}..."):
                    adapted_text = await ai_service.adapt_text_level(clean_text, language_level)
            else:
                adapted_text = clean_text
            
            # Extract title and save to Supabase
            title = extract_title(adapted_text)
            article_id = save_article(
                supabase,
                title=title,
                url=url,
                content=adapted_text,
                language_level=language_level if language_level != "No changes" else None
            )
            
            AppState.update_article(
                content=adapted_text,
                url=url,
                level=language_level,
                title=title
            )
            st.session_state.show_article = True
            st.success("Article processed successfully!")
            
    except Exception as e:
        st.error(f"Error processing article: {str(e)}")
        logging.error(f"Error processing article: {str(e)}", exc_info=True)

@async_handler
async def generate_quiz(ai_service, questions_count: int):
    """Generating quiz"""
    try:
        with st.spinner("Generating questions..."):
            article = st.session_state.article
            quiz = await ai_service.generate_quiz(
                article.content,
                questions_count,
                article.language_level
            )
            
            if quiz:
                AppState.update_quiz(quiz)
                st.session_state.article_expanded = False
                st.success("Quiz generated successfully!")
                
    except Exception as e:
        st.error(f"Error generating quiz: {str(e)}")
        logging.error(f"Error generating quiz: {str(e)}", exc_info=True)

# Run the app
if __name__ == "__main__":
    teacher_ui()
