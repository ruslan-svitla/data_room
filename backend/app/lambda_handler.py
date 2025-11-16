"""
AWS Lambda handler for FastAPI application.
Uses Mangum adapter to convert API Gateway events to FastAPI requests.
"""

import logging
import os
import sys

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Set up necessary environment variables for Lambda
os.environ["PYTHONPATH"] = os.getcwd()
logger.info(f"PYTHONPATH set to: {os.environ.get('PYTHONPATH')}")

logger.info(f"Python version: {sys.version}")
logger.info(f"Current directory: {os.getcwd()}")
logger.info(f"Directory contents: {os.listdir(os.getcwd())}")

try:
    # Import Mangum for API Gateway integration
    from mangum import Mangum

    logger.info("Mangum imported successfully")

    # Import the app
    from app.main import app

    logger.info("Application imported successfully")

    # Create Mangum handler
    handler = Mangum(app, lifespan="off")
    logger.info("Mangum handler created successfully")

except Exception as e:
    logger.error(f"Initialization error: {str(e)}")
    # Re-raise for Lambda to report the error properly
    raise
