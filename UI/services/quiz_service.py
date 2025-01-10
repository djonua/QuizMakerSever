import streamlit as st
import asyncio
from typing import Dict, List, Optional
from ..state.app_state import AppState
from ..db_service import save_test
import logging

logger = logging.getLogger(__name__)

class QuizService:
    """Сервис для работы с викториной"""
    
    def __init__(self, ai_service):
        self.ai_service = ai_service
        logger.info(f"QuizService initialized with ai_service: {ai_service}")
    
    async def generate_quiz(self, text: str, count: int, level: Optional[str] = None) -> List[Dict]:
        """Генерация викторины"""
        logger.info(f"QuizService.generate_quiz called with text: {text}, count: {count}, level: {level}")
        quiz = await self.ai_service.generate_quiz(text, count, level)
        if quiz:
            AppState.update_quiz(quiz)
        logger.info(f"Returning quiz: {quiz}")
        return quiz
    
    async def regenerate_question(self, 
                                text: str, 
                                index: int, 
                                current_quiz: List[Dict],
                                level: Optional[str] = None) -> Dict:
        """Регенерация отдельного вопроса"""
        logger.info(f"QuizService.regenerate_question called with index: {index}, level: {level}")
        logger.info(f"Text length: {len(text)}, Current quiz questions: {len(current_quiz)}")
        
        # Преобразуем формат вопросов для AI сервиса
        current_questions_ai_format = []
        for q in current_quiz:
            current_questions_ai_format.append({
                "question": q.get("question_text", ""),
                "options": q.get("options", []),
                "correct_answer": q.get("correct_answer", "")
            })
        
        # Получаем новый вопрос от AI
        logger.info("Calling AI service")
        new_question = await self.ai_service.regenerate_question(
            text,
            index,
            current_questions_ai_format,
            level if level != "No changes" else None
        )
        logger.info(f"Got response from AI service: {new_question}")
        
        if new_question:
            # Преобразуем формат ответа AI в формат базы данных
            result = {
                "question_text": new_question["question"],
                "options": new_question["options"],
                "correct_answer": new_question["correct_answer"]
            }
            logger.info(f"Returning formatted question: {result}")
            return result
        return None
    
    async def save_quiz(self, supabase, title: str, teacher_id: str = "default") -> bool:
        """Сохранение викторины"""
        logger.info(f"QuizService.save_quiz called with title: {title}, teacher_id: {teacher_id}")
        quiz = st.session_state.quiz
        article = st.session_state.article
        
        if not quiz or not quiz.questions:
            st.error("No quiz to save")
            logger.error("No quiz to save")
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
                logger.info("Quiz saved successfully!")
                return True
            else:
                st.error("Failed to save quiz")
                logger.error("Failed to save quiz")
                return False
            
        except Exception as e:
            st.error(f"Failed to save quiz: {str(e)}")
            logger.error(f"Failed to save quiz: {str(e)}")
            return False
