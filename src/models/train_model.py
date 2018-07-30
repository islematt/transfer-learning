import os

from rx.subjects import Subject
from send2trash import send2trash

from src.utils.file_utils import absolute_path_of

class TrainModel:
    model_update = Subject()

    def __init__(self, dir_path):
        self.dir_path = dir_path

    @property
    def name(self):
        return os.path.basename(self.dir_path)

    def delete(self):
        send2trash(self.dir_path)
        TrainModel._notify_model_update()

    @staticmethod
    def _notify_model_update():
        TrainModel.model_update.on_next(TrainModel.load())

    @staticmethod
    def load():
        trained_models_path = absolute_path_of('trained_models')

        entries = os.listdir(trained_models_path)
        abs_entry_paths = [os.path.join(trained_models_path, entry) for entry in entries]
        dir_entry_paths = list(filter(lambda entry_path: os.path.isdir(entry_path), abs_entry_paths))
        models = [TrainModel(dir_entry_path) for dir_entry_path in dir_entry_paths]

        return models