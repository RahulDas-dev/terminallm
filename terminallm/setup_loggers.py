import logging
import logging.handlers
import os
from datetime import datetime
from pathlib import Path

from lib.config import Config


def setup_logger_for_cli(config: Config) -> None:
    """
    Returns a logger with the specified name, configured to output to stdout.
    This ensures consistent logging across the application.
    """

    if not config.debug:
        logging.getLogger("LiteLLM").setLevel(logging.CRITICAL + 1)
        logging.getLogger("httpx").setLevel(logging.WARNING)
        os.environ["LITELLM_LOG"] = "ERROR"
    else:
        os.environ["LITELLM_LOG"] = "INFO"

    if Path(config.log_directory).exists():
        logfile = Path(config.log_directory) / f"llm_coder_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.log"
    else:
        logfile = Path.cwd() / f"llm_coder_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.log"

    # handler.setFormatter(ColorFormatter())
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.handlers.RotatingFileHandler(
                logfile,
                maxBytes=10 * 1024 * 1024,  # 10 MB
                backupCount=5,
                encoding="utf-8",
            )
        ],
    )
