import logging
import requests

logger = logging.getLogger(__name__)

def extract_title(text: str) -> str:
    """Extracts title from markdown text"""
    try:
        lines = text.split('\n')
        for line in lines:
            if line.startswith('# '):
                return line.replace('# ', '').strip()
        return "Untitled"
    except Exception as e:
        logger.error(f"Error extracting title: {str(e)}", exc_info=True)
        return "Untitled"

def fetch_article(url: str) -> str:
    """Fetches article from URL"""
    logger.info(f"Fetching article from URL: {url}")
    try:
        response = requests.get(url)
        response.raise_for_status()
        logger.info(f"Article fetched successfully, content length: {len(response.text)}")
        return response.text
    except Exception as e:
        logger.error(f"Error fetching article: {str(e)}", exc_info=True)
        raise
