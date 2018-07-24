import os
import logging

def ensure_dir_exists(dir_path):
    if not os.path.exists(dir_path):
        logging.getLogger('app').info('Directory {} does not exist. Creating...'.format(dir_path))
        os.makedirs(dir_path)
