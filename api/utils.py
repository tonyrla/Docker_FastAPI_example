import logging
import platform
from loguru import logger
from api.api import Settings

if "Windows" not in platform.system():
    from gunicorn.app.base import BaseApplication
    from gunicorn.glogging import Logger


class InterceptHandler(logging.Handler):
    def emit(self, record):
        # Get corresponding Loguru level if it exists
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Find caller from where originated the logged message
        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


if "Windows" not in platform.system():

    class StubbedGunicornLogger(Logger):
        def setup(self, cfg):
            settings = Settings()
            handler = logging.NullHandler()
            self.error_logger = logging.getLogger("gunicorn.error")
            self.error_logger.addHandler(handler)
            self.access_logger = logging.getLogger("gunicorn.access")
            self.access_logger.addHandler(handler)
            self.error_logger.setLevel(settings.LOG_LEVEL)
            self.access_logger.setLevel(settings.LOG_LEVEL)

    class GunicornRunner(BaseApplication):
        def __init__(self, app, options=None):
            self.options = options or {}
            self.application = app
            super().__init__()

        def load_config(self):
            config = {
                key: value
                for key, value in self.options.items()
                if key in self.cfg.settings and value is not None
            }
            for key, value in config.items():
                self.cfg.set(key.lower(), value)

        def load(self):
            return self.application
