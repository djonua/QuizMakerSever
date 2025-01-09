import sys
import os
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()  # Output to console
    ]
)
logger = logging.getLogger(__name__)

logger.info("Starting teacher app...")
logger.info(f"Python version: {sys.version}")
logger.info(f"Current working directory: {os.getcwd()}")

# Add the project root directory to the import path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)
logger.info(f"Added to Python path: {current_dir}")
logger.info(f"Python path: {sys.path}")

try:
    logger.info("Attempting to import UI module...")
    from UI.teacher_ui import teacher_ui
    logger.info("UI module imported successfully")
except Exception as e:
    logger.error(f"Failed to import UI module: {str(e)}", exc_info=True)
    raise

def main():
    teacher_ui()

if __name__ == "__main__":
    logger.info("Starting main application...")
    try:
        main()
        logger.info("Application finished successfully")
    except Exception as e:
        logger.error(f"Fatal error in main application: {str(e)}", exc_info=True)
        print(f"A critical error occurred in the application: {str(e)}")
