import requests

from src.utils.class_utils import Singleton


# TODO: Deal with this warning
# noinspection PyCompatibility
class Session(metaclass=Singleton):
    _shared = None

    @classmethod
    def shared(cls):
        return cls._shared

    @classmethod
    def create(cls):
        if not cls._shared:
            cls._shared = requests.Session()
        return cls._shared

    @classmethod
    def dispose(cls):
        if cls._shared:
            cls._shared.close()
            cls._shared = None
