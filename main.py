"""
Main entry point for the Automated Report Extraction System.
"""

import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core.logging_config import setup_logging, get_logger
from core.utils import load_config
from core.exceptions import handle_error, LangExtractorError


def main():
    """Main application entry point."""
    try:
        # Load configuration
        config = load_config()
        
        # Setup logging
        setup_logging({
            'log_level': config.log_level,
            'console_logging': True,
            'structured_logging': False
        })
        
        logger = get_logger(__name__)
        logger.info("Starting Automated Report Extraction System")
        
        # TODO: Initialize GUI application
        logger.info("Application initialized successfully")
        
    except LangExtractorError as e:
        print(f"Application Error: {e.get_user_message()}")
        sys.exit(1)
    except Exception as e:
        logger = get_logger(__name__)
        handled_error = handle_error(e, logger)
        print(f"Unexpected Error: {handled_error.get_user_message()}")
        sys.exit(1)


if __name__ == "__main__":
    main()