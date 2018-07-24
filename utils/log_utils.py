import os
import logging, logging.config
import json

import tensorflow as tf


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
