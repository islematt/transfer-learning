import os
import logging
import logging.config
import json

import tensorflow as tf


# noinspection PyUnresolvedReferences
class QuiteStreamHandler(logging.StreamHandler):
    def emit(self, record):
        if 'Initialize variable' in record.msg and 'from checkpoint' in record.msg:
            return
        if hasattr(self, 'proxy'):
            self.proxy(self.formatter.format(record))
            return

        super(QuiteStreamHandler, self).emit(record)


def setup_logging(default_path='logging.json', default_level=logging.INFO, env_log_key='LOG_CFG'):
    log_file_path = os.getenv(env_log_key, default_path)
    try:
        with open(log_file_path, 'rt') as f:
            config = json.load(f)
        logging.config.dictConfig(config)
    except Exception as e:
        logging.basicConfig(level=default_level)


def bridge_tf_log():
    logger = logging.getLogger('app')

    tf.logging.set_verbosity(tf.logging.DEBUG)
    tf_logger = logging.getLogger('tensorflow')
    tf_logger.handlers = []
    for handler in logger.handlers:
        tf_logger.addHandler(handler)


def redirect_console_to(proxy):
    handler = _get_console_handler()
    if not handler:
        return

    handler.proxy = proxy
    print(handler.proxy)


def _get_console_handler():
    for handler in logging.getLogger('app').handlers:
        if isinstance(handler, QuiteStreamHandler):
            return handler

    return None
