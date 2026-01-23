from loguru import logger
import logging
import sys
import os

# LOG_LEVELs
# INFO
# DEBUG
# TRACE
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")


def format_record(record):
    """Extract only the main module name from the full module path."""
    # Get the full module name (e.g., 'database.migrations')
    full_name = record["name"]
    # Extract only the first part (e.g., 'database')
    main_module = full_name.split(".")[0] if "." in full_name else full_name
    # Store it back in the record
    record["extra"]["main_module"] = main_module
    return record


class InterceptHandler(logging.Handler):
    def emit(self, record):
        # Get corresponding Loguru level if it exists
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Find caller from where originated the logged message
        frame, depth = logging.currentframe(), 2
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


# Configure intercept handler for standard logging
# Explicit replace handlers of specific loggers
def setup_logging_intercept():
    """Setup interception of standard Python logging to Loguru."""
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)

    # Intercept specific loggers
    for logger_name in [
        "uvicorn",
        "uvicorn.access",
        "uvicorn.error",
        "alembic",
        "sqlalchemy",
    ]:
        logging_logger = logging.getLogger(logger_name)
        logging_logger.handlers = [InterceptHandler()]
        logging_logger.propagate = False


# Start logger
if LOG_LEVEL == "TRACE":
    logger.remove()
    logger = logger.patch(format_record)
    logger.add(
        sys.stdout,
        colorize=True,
        level="TRACE",
        format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{extra[main_module]: <12}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | <level>{message}</level>",
        backtrace=True,
        diagnose=True,
    )
    setup_logging_intercept()
    logger.warning("logger level set to TRACE with full debugging")

elif LOG_LEVEL == "DEBUG":
    logger.remove()
    logger = logger.patch(format_record)
    logger.add(
        sys.stdout,
        colorize=True,
        level="DEBUG",
        format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{extra[main_module]: <12}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | <level>{message}</level>",
        backtrace=True,
        diagnose=False,
    )
    setup_logging_intercept()
    logger.info("logger level set to DEBUG")

else:
    logger.remove()
    logger = logger.patch(format_record)
    logger.add(
        sys.stdout,
        colorize=True,
        level="INFO",
        format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{extra[main_module]: <10}</cyan> | <level>{message}</level>",
        backtrace=True,
        diagnose=False,
    )
    setup_logging_intercept()
    logger.info("logger level set to INFO")
