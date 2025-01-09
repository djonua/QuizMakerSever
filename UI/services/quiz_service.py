import streamlit as st
import asyncio
from typing import Dict, List, Optional
from ..state.app_state import AppState
from ..db_service import save_test

class QuizService:
    """Сервис для работы с викториной"""
    
    def __init__(self, ai_service):
        self.ai_service = ai_service
    
    async def generate_quiz(self, text: str, count: int, level: Optional[str] = None) -> List[Dict]:
        """Генерация викторины"""
        quiz = await self.ai_service.generate_quiz(text, count, level)
        if quiz:
            AppState.update_quiz(quiz)
        return quiz
    
    async def regenerate_question(self, 
                                text: str, 
                                index: int, 
                                current_quiz: List[Dict],
                                level: Optional[str] = None) -> Dict:
        """Регенерация отдельного вопроса"""
        return await self.ai_service.regenerate_question(
            text,
            index,
            current_quiz,
            level if level != "No changes" else None
        )
    
    async def save_quiz(self, supabase, title: str, teacher_id: str = "default") -> bool:
        """Сохранение викторины"""
        quiz = st.session_state.quiz
        article = st.session_state.article
        
        if not quiz or not quiz.questions:
            st.error("No quiz to save")
            return False
            
        try:
            # Преобразуем "No changes" в "original" для базы данных
            language_level = "original"
            if article.language_level:
                language_level = "original" if article.language_level == "No changes" else article.language_level
            
            # Сохраняем тест в базу данных
            test_id = await save_test(
                supabase=supabase,
                title=title,
                url=article.url,
                content=article.content,
                language_level=language_level,
                questions=quiz.questions,
                teacher_id=teacher_id
            )
            
            if test_id:
                # Очищаем состояние после успешного сохранения
                AppState.clear_state()
                st.success("Quiz saved successfully!")
                return True
            else:
                st.error("Failed to save quiz")
                return False
            
        except Exception as e:
            st.error(f"Failed to save quiz: {str(e)}")
            return False
