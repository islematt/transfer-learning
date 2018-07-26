import os, sys
import logging


def ensure_dir_exists(dir_path):
    if not os.path.exists(dir_path):
        logging.getLogger('app').info('Directory {} does not exist. Creating...'.format(dir_path))
        os.makedirs(dir_path)


def get_root_dir():
    main_module = sys.modules['__main__']
    return os.path.dirname(os.path.abspath(main_module.__file__))


def absolute_path_of(path_obj):
    root_dir = get_root_dir()
    prepend_root_dir = lambda p: os.path.join(root_dir, p)
    if isinstance(path_obj, str):
        return prepend_root_dir(path_obj)
    elif isinstance(path_obj, list):
        return [prepend_root_dir(p) for p in path_obj]

    raise ValueError('Unsupported argument type: {}'.format(type(path_obj)))
