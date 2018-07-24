import logging

import tensorflow as tf

from image_matcher import match
from utils import log_utils
import logging

logger = logging.getLogger('app')


def main():
    log_utils.setup_logging()
    log_utils.bridge_tf_log()

    match_results = match(2, 2)
    logger.info("Match results:")
    for file_name, labels, probabilities in match_results:
        msg = '\n'.join(["\t{}: {}".format(label, probability) for label, probability in zip(labels, probabilities)])
        logger.info('\n{}: \n{}'.format(file_name, msg))


if __name__ == '__main__':
    main()
