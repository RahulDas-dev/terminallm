import logging

from termcolor import colored


class ColorFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        color = getattr(record, "color", None)
        message = super().format(record)
        if color:
            message = colored(message, color)
        return message


def modify_logger_behaviour(name: str) -> logging.Logger:
    root_handlers = logging.getLogger().handlers
    current_logger = logging.getLogger(name)
    if not root_handlers:
        new_handler = logging.StreamHandler()
        new_handler.terminator = ""
        new_handler.setFormatter(ColorFormatter("%(message)s"))
        current_logger.addHandler(new_handler)
        current_logger.propagate = False
        current_logger.setLevel(logging.INFO)
        return current_logger

    # Remove  exixting Handlers from the current logger
    for handler in current_logger.handlers[:]:
        current_logger.removeHandler(handler)

    for handler_r in root_handlers:
        if type(handler_r) is logging.StreamHandler:
            new_handler = logging.StreamHandler()
            new_handler.terminator = ""
            new_handler.setFormatter(ColorFormatter("%(message)s"))
            current_logger.addHandler(new_handler)
        elif type(handler_r) is logging.FileHandler:
            new_handler = logging.FileHandler(
                handler_r.baseFilename,
                handler_r.mode,
                handler_r.encoding,
                handler_r.delay,
                handler_r.errors,
            )
            new_handler.terminator = ""
            new_handler.setFormatter(logging.Formatter("%(message)s"))
            current_logger.addHandler(new_handler)
        else:
            continue
    current_logger.propagate = False
    return current_logger
