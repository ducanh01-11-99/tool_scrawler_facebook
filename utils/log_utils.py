import logging

class CustomFormatter(logging.Formatter):

    grey = "\x1b[38;20m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    green = "\x1b[32;20m"
    blue = "\x1b[36;20m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"

    format = "%(asctime)s - %(levelname).1s - %(filename)s:%(lineno)d - %(funcName)s - %(message)s"

    FORMATS = {
        logging.DEBUG: grey + format + reset,
        logging.INFO: green + format + reset,
        logging.WARNING: yellow + format + reset,
        logging.ERROR: red + format + reset,
        logging.CRITICAL: bold_red + format + reset
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)




logger: logging.Logger = logging.getLogger('logger')
logger.setLevel(logging.DEBUG)
#formatter = logging.Formatter('%(asctime)s - %(levelname).1s - %(filename)s:%(lineno)d - %(funcName)s - %(message)s')
console_handler = logging.StreamHandler()
#console_handler.setFormatter(formatter)
console_handler.setFormatter(CustomFormatter())
logger.addHandler(console_handler)
