import logging
from datetime import datetime
import json
import random
import string
from typing import Optional, Dict, List
from supabase import Client

logger = logging.getLogger(__name__)

def generate_access_code() -> str:
    """Generate a random 5-character access code"""
    chars = string.ascii_uppercase + string.digits  # A-Z and 0-9
    return ''.join(random.choices(chars, k=5))

async def save_test(supabase: Client, title: str, url: str, content: str, language_level: str, questions: List[Dict], teacher_id: str) -> str:
    """Save test to Supabase"""
    try:
        # Use article title or first 30 characters of content
        if not title:
            title = content[:30] + "..." if len(content) > 30 else content
        else:
            title = title.strip()
            if title == "":
                title = content[:30] + "..." if len(content) > 30 else content
        
        logger.info(f"Saving test: {title}")
        
        # Generate unique access code
        while True:
            access_code = generate_access_code()
            # Check if code already exists
            result = supabase.table("tests").select("id").eq("access_code", access_code).execute()
            if not result.data:
                break
        
        # Save test
        test_data = {
            "title": title,
            "article_url": url,
            "article_text": content,
            "language_level": language_level if language_level != "No changes" else "original",
            "teacher_id": teacher_id,
            "created_at": datetime.utcnow().isoformat(),
            "access_code": access_code
        }
        
        result = supabase.table("tests").insert(test_data).execute()
        test_id = result.data[0]["id"] if result and hasattr(result, 'data') and result.data else None
        
        if not test_id:
            raise Exception("Failed to get test ID after saving")
            
        logger.info(f"Test saved with ID: {test_id}, access code: {access_code}")
        
        # Save questions
        for i, question in enumerate(questions):
            question_data = {
                "test_id": test_id,
                "question_text": question.get("question"),
                "correct_answer": question.get("correct_answer"),
                "options": json.dumps(question.get("options", [])),
                "order_number": i
            }
            question_result = supabase.table("questions").insert(question_data).execute()
            if not question_result or not hasattr(question_result, 'data') or not question_result.data:
                logger.error(f"Failed to save question {i+1}")
                
        return test_id
    except Exception as e:
        logger.error(f"Error saving test: {str(e)}", exc_info=True)
        raise

def save_article(supabase: Client, title: str, url: str, content: str, language_level: Optional[str] = None) -> int:
    """Saves article to Supabase if it doesn't exist with same URL and language level"""
    try:
        # Check if article with same URL and language level exists
        logger.info(f"Checking for existing article with URL: {url} and level: {language_level}")
        
        # Base query
        query = supabase.table("article_history")\
            .select("*")\
            .eq("url", url)\
            .eq("is_deleted", False)
            
        # Add language level filter
        if language_level is not None:
            result = query.eq("language_level", language_level).execute()
        else:
            result = query.filter("language_level", "is", "null").execute()
            
        logger.info(f"Found {len(result.data if result and hasattr(result, 'data') else [])} matching articles")
        
        # If article exists, return its ID
        if result and hasattr(result, 'data') and result.data:
            logger.info(f"Article already exists with ID: {result.data[0]['id']}")
            # Update content and title if they changed
            if result.data[0]['content'] != content or result.data[0]['title'] != title:
                logger.info("Content or title changed, updating existing article")
                supabase.table("article_history")\
                    .update({"content": content, "title": title})\
                    .eq("id", result.data[0]["id"])\
                    .execute()
            return result.data[0]["id"]
        
        # If article doesn't exist, save it
        logger.info("Creating new article")
        data = {
            "title": title,
            "url": url,
            "content": content,
            "language_level": language_level,
            "created_at": datetime.utcnow().isoformat()
        }
        result = supabase.table("article_history").insert(data).execute()
        logger.info(f"Created new article with ID: {result.data[0]['id'] if result and hasattr(result, 'data') and result.data else None}")
        return result.data[0]["id"] if result and hasattr(result, 'data') and result.data else None
    except Exception as e:
        logger.error(f"Error saving article: {str(e)}", exc_info=True)
        raise

def get_article_history(supabase: Client) -> List[Dict]:
    """Gets article history from Supabase"""
    try:
        logger.info("Getting article history...")
        result = supabase.table('article_history')\
            .select('*')\
            .order('created_at', desc=True)\
            .limit(10)\
            .execute()
        
        history = result.data if result and hasattr(result, 'data') else []
        logger.info(f"Got {len(history)} articles from history")
        return history
    except Exception as e:
        logger.error(f"Error getting article history: {str(e)}", exc_info=True)
        return []

def get_article_by_id(supabase: Client, article_id: int) -> Optional[Dict]:
    """Gets article by ID from Supabase"""
    try:
        result = supabase.table("article_history")\
            .select("*")\
            .eq("id", article_id)\
            .eq("is_deleted", False)\
            .limit(1)\
            .execute()
        return result.data[0] if result and hasattr(result, 'data') and result.data else None
    except Exception as e:
        logger.error(f"Error getting article by id: {str(e)}", exc_info=True)
        return None

def load_teacher_tests(supabase: Client, teacher_id: str) -> List[Dict]:
    """
    Loads all tests for the teacher
    """
    try:
        logger.info(f"Loading tests for teacher: {teacher_id}")
        result = supabase.table("tests")\
            .select("*, questions!inner(count)")\
            .eq("teacher_id", teacher_id)\
            .order("created_at", desc=True)\
            .execute()
            
        tests = result.data if result and hasattr(result, 'data') else []
        logger.info(f"Loaded {len(tests)} tests")
        return tests
    except Exception as e:
        logger.error(f"Error loading tests: {str(e)}", exc_info=True)
        return []

def test_supabase_connection(supabase: Client):
    """Test connection to Supabase"""
    try:
        result = supabase.table("tests").select("count").limit(1).execute()
        logger.info("Supabase connection test successful")
        return True
    except Exception as e:
        logger.error(f"Supabase connection test failed: {str(e)}", exc_info=True)
        return False
