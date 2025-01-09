import os
from typing import List, Dict, Optional
import openai
from dotenv import load_dotenv
from bs4 import BeautifulSoup
import re
import logging
import json

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

# Check for required environment variables
REQUIRED_ENV_VARS = ["DEEPSEEK_API_KEY", "DEEPSEEK_API_BASE", "DEEPSEEK_API_MODEL"]
missing_vars = [var for var in REQUIRED_ENV_VARS if not os.getenv(var)]
if missing_vars:
    error_msg = f"Missing required environment variables: {', '.join(missing_vars)}"
    logger.error(error_msg)
    raise Exception(error_msg)

# Configure OpenAI with DeepSeek parameters
openai.api_key = os.getenv("DEEPSEEK_API_KEY")
openai.api_base = os.getenv("DEEPSEEK_API_BASE")
MODEL = os.getenv("DEEPSEEK_API_MODEL")

logger.info(f"AI Service initialized with:")
logger.info(f"Model: {MODEL}")
logger.info(f"API Base: {openai.api_base}")
logger.info(f"API Key length: {len(openai.api_key) if openai.api_key else 0}")

async def test_ai_connection():
    """Tests connection to AI API"""
    try:
        logger.info("Testing AI connection...")
        response = await openai.ChatCompletion.acreate(
            model=MODEL,
            messages=[
                {"role": "system", "content": "Test connection"},
                {"role": "user", "content": "Say 'Connection successful'"}
            ],
            temperature=0.3
        )
        logger.info(f"Test response: {response}")
        return True
    except Exception as e:
        logger.error(f"Failed to connect to AI API: {str(e)}", exc_info=True)
        raise Exception(f"Failed to connect to AI API: {str(e)}")

class AIService:
    def __init__(self):
        self.model = MODEL
        logger.info("AIService instance created")
        
    def _preprocess_html(self, html_content: str) -> str:
        """
        Preprocesses HTML to extract text
        """
        try:
            logger.debug(f"Starting HTML preprocessing. Content length: {len(html_content)}")
            
            # Create BeautifulSoup object
            soup = BeautifulSoup(html_content, 'html.parser')
            logger.debug("BeautifulSoup parser created")
            
            # Remove unnecessary tags
            for tag in soup(['script', 'style', 'header', 'footer', 'nav', 'aside', 'meta', 'link', 'iframe']):
                tag.decompose()
            logger.debug("Unnecessary tags removed")
            
            # Get text
            text = soup.get_text(separator='\n', strip=True)
            logger.debug(f"Text extracted, length: {len(text)}")
            
            # Remove extra spaces and line breaks
            text = re.sub(r'\s+', ' ', text)
            text = re.sub(r'\n\s*\n', '\n\n', text)
            
            result = text.strip()
            logger.debug(f"Preprocessing completed. Final text length: {len(result)}")
            logger.debug("First 500 chars of preprocessed text:")
            logger.debug(result[:500])
            return result
            
        except Exception as e:
            logger.error(f"Error in HTML preprocessing: {str(e)}", exc_info=True)
            raise Exception("Failed to preprocess HTML")
        
    async def clean_article(self, html_content: str) -> str:
        """
        Cleans HTML content, extracting only the main article text
        """
        try:
            logger.info("Starting article cleaning")
            
            # First preprocess HTML
            preprocessed_text = self._preprocess_html(html_content)
            logger.debug(f"Preprocessed text length: {len(preprocessed_text)}")
            
            # Ограничиваем размер текста
            max_chars = 32000
            if len(preprocessed_text) > max_chars:
                logger.warning(f"Text too long ({len(preprocessed_text)} chars), truncating to {max_chars}")
                preprocessed_text = preprocessed_text[:max_chars]
            
            # Test AI connection
            await test_ai_connection()
            
            logger.info("Sending request to AI for cleaning")
            try:
                response = await openai.ChatCompletion.acreate(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": """You are a text extraction and formatting expert. Your task:
1. Find and return only the main article text without changing or rearranging phrases
2. Remove all technical information, ads, menus, and other elements
3. Format the text as follows:
   - Article title should be in format: # Title
   - Subtitles in format: ## Subtitle
   - Separate paragraphs with empty line
   - Preserve lists and important formatting elements
   - Use **bold text** for important phrases
   
Return the text in Markdown format."""},
                        {"role": "user", "content": f"Find, clean and format the main article text from the following content:\n\n{preprocessed_text}"}
                    ],
                    temperature=0.3
                )
                logger.debug(f"Raw AI Response: {json.dumps(response, indent=2)}")
                
                if not response or not response.choices:
                    raise Exception("AI returned empty response")
                    
                cleaned_text = response.choices[0].message.content
                logger.debug(f"Cleaned text length: {len(cleaned_text)}")
                logger.debug("First 500 chars of cleaned text:")
                logger.debug(cleaned_text[:500])
                
                if not cleaned_text or len(cleaned_text.strip()) < 50:
                    logger.error("AI returned too short or empty text")
                    raise Exception("AI returned too short or empty text")
                    
                logger.info("Article cleaning completed successfully")
                return cleaned_text
                
            except openai.error.OpenAIError as e:
                logger.error(f"OpenAI API error: {str(e)}", exc_info=True)
                raise Exception(f"DeepSeek API error: {str(e)}")
                
        except Exception as e:
            logger.error(f"Error in article cleaning: {str(e)}", exc_info=True)
            raise Exception(f"Failed to process text through AI: {str(e)}")

    async def adapt_text_level(self, text: str, target_level: str) -> str:
        """
        Adapts text to the specified language level
        """
        if target_level == "original" or target_level == "No changes":
            logger.info("No adaptation needed, returning original text")
            return text
            
        try:
            logger.info(f"Starting text adaptation to level {target_level}")
            
            response = await openai.ChatCompletion.acreate(
                model=self.model,
                messages=[
                    {"role": "system", "content": f"""You are a language adaptation expert. Your task:
1. Adapt the text to {target_level} level while preserving the meaning
2. Simplify vocabulary and grammar according to {target_level} requirements
3. Keep the text natural and engaging
4. Preserve Markdown formatting
5. Do not change or remove important information

Return the adapted text in Markdown format."""},
                    {"role": "user", "content": f"Adapt this text to {target_level} level:\n\n{text}"}
                ],
                temperature=0.3
            )
            
            if not response or not response.choices:
                raise Exception("AI returned empty response")
                
            adapted_text = response.choices[0].message.content
            
            if not adapted_text or len(adapted_text.strip()) < 50:
                raise Exception("AI returned too short or empty text")
                
            logger.info("Text adaptation completed successfully")
            return adapted_text
            
        except Exception as e:
            logger.error(f"Error in text adaptation: {str(e)}", exc_info=True)
            raise Exception(f"Failed to adapt text: {str(e)}")

    async def generate_quiz(self, text: str, questions_count: int = 5, language_level: str = None) -> List[Dict]:
        """
        Generates quiz questions based on the text
        """
        try:
            logger.info(f"Starting quiz generation, questions: {questions_count}, level: {language_level}")
            
            level_instruction = f"at {language_level} level" if language_level and language_level != "No changes" else ""
            
            response = await openai.ChatCompletion.acreate(
                model=self.model,
                messages=[
                    {"role": "system", "content": f"""You are a quiz generation expert. Your task:
1. Create {questions_count} multiple-choice questions based on the text {level_instruction}
2. Each question should:
   - Test understanding of important information from the text
   - Have 4 answer options
   - Have only one correct answer
   - Be clear and unambiguous
3. Return questions in VALID JSON format like this:
[
  {{
    "question": "What is the main topic of the text?",
    "options": [
      "First option",
      "Second option",
      "Third option",
      "Fourth option"
    ],
    "correct_answer": "First option"
  }}
]
IMPORTANT: Make sure to use double quotes for strings and escape special characters properly!"""},
                    {"role": "user", "content": f"Generate {questions_count} questions based on this text:\n\n{text}"}
                ],
                temperature=0.7
            )
            
            if not response or not response.choices:
                raise Exception("AI returned empty response")
                
            quiz_text = response.choices[0].message.content.strip()
            logger.info("Raw quiz response:")
            logger.info(quiz_text)
            
            try:
                # Try to find JSON array in the response
                match = re.search(r'\[[\s\S]*\]', quiz_text)
                if match:
                    quiz_text = match.group(0)
                    logger.info("Extracted JSON array:")
                    logger.info(quiz_text)
                
                # Parse JSON response
                quiz = json.loads(quiz_text)
                
                # Validate quiz format
                if not isinstance(quiz, list):
                    raise Exception("Quiz must be a list")
                if len(quiz) == 0:
                    raise Exception("Quiz is empty")
                    
                # Validate each question
                for i, q in enumerate(quiz):
                    if not isinstance(q, dict):
                        raise Exception(f"Question {i} is not a dictionary")
                    if "question" not in q:
                        raise Exception(f"Question {i} has no 'question' field")
                    if "options" not in q:
                        raise Exception(f"Question {i} has no 'options' field")
                    if "correct_answer" not in q:
                        raise Exception(f"Question {i} has no 'correct_answer' field")
                    if not isinstance(q["options"], list):
                        raise Exception(f"Question {i} options is not a list")
                    if len(q["options"]) != 4:
                        raise Exception(f"Question {i} must have exactly 4 options")
                    if q["correct_answer"] not in q["options"]:
                        raise Exception(f"Question {i} correct answer not in options")
                    
                logger.info(f"Generated and validated {len(quiz)} questions successfully")
                return quiz
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse quiz JSON: {str(e)}")
                logger.error(f"Invalid JSON: {quiz_text}")
                raise Exception("Failed to parse quiz response - invalid JSON format")
            except Exception as e:
                logger.error(f"Quiz validation error: {str(e)}")
                raise Exception(f"Invalid quiz format: {str(e)}")
                
        except Exception as e:
            logger.error(f"Error in quiz generation: {str(e)}", exc_info=True)
            raise Exception(f"Failed to generate quiz: {str(e)}")

    async def regenerate_question(self, text: str, question_index: int, current_questions: List[Dict], language_level: str = None) -> Dict:
        """
        Regenerates a single quiz question based on the text, avoiding duplicates with existing questions
        """
        try:
            logger.info(f"Starting single question regeneration, index: {question_index}, level: {language_level}")
            
            # Format existing questions for prompt
            existing_questions = []
            for i, q in enumerate(current_questions):
                if i != question_index:  # Skip the question we're regenerating
                    existing_questions.append(f"{i+1}. {q['question']}")
            existing_questions_text = "\n".join(existing_questions)
            
            level_instruction = f"at {language_level} level" if language_level and language_level != "No changes" else ""
            
            response = await openai.ChatCompletion.acreate(
                model=self.model,
                messages=[
                    {"role": "system", "content": f"""You are a quiz generation expert. Your task:
1. Create 1 multiple-choice question based on the text {level_instruction}
2. The question should:
   - Test understanding of important information from the text
   - Have 4 answer options
   - Have only one correct answer
   - Be clear and unambiguous
   - Be DIFFERENT from these existing questions:
{existing_questions_text}
3. Return the question in VALID JSON format like this:
{{
  "question": "What is the main topic of the text?",
  "options": [
    "First option",
    "Second option",
    "Third option",
    "Fourth option"
  ],
  "correct_answer": "First option"
}}
IMPORTANT: Make sure to use double quotes for strings and escape special characters properly!"""},
                    {"role": "user", "content": f"Generate a new question based on this text:\n\n{text}"}
                ],
                temperature=0.7
            )
            
            if not response or not response.choices:
                raise Exception("AI returned empty response")
                
            quiz_text = response.choices[0].message.content.strip()
            logger.info("Raw question response:")
            logger.info(quiz_text)
            
            try:
                # Try to find JSON object in the response
                match = re.search(r'\{[\s\S]*\}', quiz_text)
                if match:
                    quiz_text = match.group(0)
                    logger.info("Extracted JSON object:")
                    logger.info(quiz_text)
                
                # Parse JSON response
                question = json.loads(quiz_text)
                
                # Validate question format
                if not isinstance(question, dict):
                    raise Exception("Question must be a dictionary")
                
                # Validate question fields
                if "question" not in question:
                    raise Exception("Question has no 'question' field")
                if "options" not in question:
                    raise Exception("Question has no 'options' field")
                if "correct_answer" not in question:
                    raise Exception("Question has no 'correct_answer' field")
                if not isinstance(question["options"], list):
                    raise Exception("Question options is not a list")
                if len(question["options"]) != 4:
                    raise Exception("Question must have exactly 4 options")
                if question["correct_answer"] not in question["options"]:
                    raise Exception("Question correct answer not in options")
                    
                logger.info("Generated and validated new question successfully")
                return question
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse question JSON: {str(e)}")
                logger.error(f"Invalid JSON: {quiz_text}")
                raise Exception("Failed to parse question response - invalid JSON format")
            except Exception as e:
                logger.error(f"Question validation error: {str(e)}")
                raise Exception(f"Invalid question format: {str(e)}")
                
        except Exception as e:
            logger.error(f"Error in question regeneration: {str(e)}", exc_info=True)
            raise Exception(f"Failed to regenerate question: {str(e)}")
