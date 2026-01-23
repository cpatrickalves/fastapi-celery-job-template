from loguru import logger
import logging
import sys
import os

# LOG_LEVELs
# INFO
# DEBUG
# TRACE
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")


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


# Start logger
if LOG_LEVEL == "TRACE":
    logging.basicConfig(handlers=[InterceptHandler()], level=0)
    logger.warning("logger level set to DEBUG with full TRACING")

elif LOG_LEVEL == "DEBUG":
    logger.remove()
    logger.add(
        sys.stdout,
        colorize=True,
        level="DEBUG",
        format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        backtrace=True,
        diagnose=False,
    )
    logger.info("logger level set to DEBUG")

elif LOG_LEVEL == "INFO":
    logger.remove()
    logger.info("logger level set to INFO")
    logger.add(
        sys.stdout,
        colorize=True,
        level="INFO",
        format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        backtrace=True,
        diagnose=False,
    )

else:
    # Handle standard Python logging levels (INFO, DEBUG, WARNING, ERROR, CRITICAL)
    logger.remove()
    logger.info(f"logger level set to {LOG_LEVEL}")
    logger.add(
        sys.stdout,
        colorize=True,
        level=LOG_LEVEL,
        format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        backtrace=True,
        diagnose=False,
    )
    logger.info(f"logger level set to {LOG_LEVEL}")
