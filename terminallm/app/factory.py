import logging

from .base import BaseEngine, TMode
from .db.database import Database
from .ios.factory import build_io_devices
from .question_answer import QnaEnginee

logger = logging.getLogger(__name__)


def build_app(mode: TMode, client_name: str = "gpt-3.5-turbo") -> BaseEngine:
    inputd, outputd = build_io_devices(mode)
    status = Database().initilize()
    if not status:
        logger.info("Database While Database Initialization")
        raise ValueError("Database While Database Initialization")
    if not Database().db_path.exists():
        logger.info(f"Database not found at {Database().db_path}")
        raise ValueError(f"Database not found at {Database().db_path}")
    return QnaEnginee(input_device=inputd, output_device=outputd, client_name=client_name)
