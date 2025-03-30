import logging

import structlog

logging.getLogger("matplotlib").setLevel(logging.INFO)
logging.getLogger("peewee").setLevel(logging.INFO)

renderer_ = [
    structlog.contextvars.merge_contextvars,
    structlog.processors.add_log_level,
    structlog.processors.StackInfoRenderer(),
    structlog.dev.set_exc_info,
    structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S", utc=False),
]

# renderer_ += [structlog.dev.ConsoleRenderer()]
renderer_ += [structlog.processors.JSONRenderer()]

structlog.configure(
    processors=renderer_,
    wrapper_class=structlog.make_filtering_bound_logger(logging.NOTSET),
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
    cache_logger_on_first_use=False,
)

logger = structlog.get_logger()

