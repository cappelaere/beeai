"""
Log formatter that matches Django's format (LEVEL TIMESTAMP NAME MESSAGE)
with colored level, for uvicorn so app and server logs look the same.
"""

import logging
import sys
from copy import copy

import click

DEFAULT_FMT = "%(levelname_colored)s %(asctime)s %(name)s %(message)s"


class DjangoStyleFormatter(logging.Formatter):
    """Format: LEVEL TIMESTAMP NAME MESSAGE (LEVEL colored like uvicorn)."""

    level_name_colors = {
        logging.DEBUG: lambda s: click.style(str(s), fg="cyan"),
        logging.INFO: lambda s: click.style(str(s), fg="green"),
        logging.WARNING: lambda s: click.style(str(s), fg="yellow"),
        logging.ERROR: lambda s: click.style(str(s), fg="red"),
        logging.CRITICAL: lambda s: click.style(str(s), fg="bright_red"),
    }

    def __init__(self, fmt=None, datefmt=None, use_colors=True, **kwargs):
        # Support both 'fmt' (uvicorn) and 'format' (dictConfig)
        fmt = fmt or kwargs.pop("format", None) or DEFAULT_FMT
        super().__init__(fmt=fmt, datefmt=datefmt)
        self.use_colors = use_colors and sys.stderr.isatty()

    def formatMessage(self, record: logging.LogRecord) -> str:
        recordcopy = copy(record)
        levelname = recordcopy.levelname
        if self.use_colors:
            func = self.level_name_colors.get(recordcopy.levelno, lambda s: s)
            levelname = func(levelname)
        recordcopy.__dict__["levelname_colored"] = levelname
        return super().formatMessage(recordcopy)
