import logging

def setup_logging():
    """Sets up logging for the application."""
    logging.basicConfig(level=logging.INFO)

    info_logger = logging.getLogger("info_logger")
    error_logger = logging.getLogger("error_logger")

    # Handlers
    info_handler = logging.FileHandler("info.log")
    error_handler = logging.FileHandler("error.log")

    # Formatter
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

    info_handler.setFormatter(formatter)
    error_handler.setFormatter(formatter)

    # Assign levels
    info_handler.setLevel(logging.INFO)
    error_handler.setLevel(logging.ERROR)

    info_logger.addHandler(info_handler)
    error_logger.addHandler(error_handler)

    return info_logger, error_logger
