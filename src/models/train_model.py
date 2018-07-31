import os

from rx.subjects import Subject
from send2trash import send2trash

from src.utils.file_utils import absolute_path_of

KEY_FILE_GRAPH = 'graph.pb'
KEY_FILE_LABELS = 'labels.txt'
KEY_FILE_SUMMARY = 'summary'
KEY_FILE_BOTTLENECK = 'bottleneck'
KEY_FILE_THUMBNAILS = 'thumbnails'
KEY_FILE_NAMES = [KEY_FILE_GRAPH, KEY_FILE_LABELS, KEY_FILE_SUMMARY, KEY_FILE_BOTTLENECK, KEY_FILE_THUMBNAILS]

IMAGE_EXTENSIONS = ['jpg', 'jpeg', 'JPG', 'JPEG', 'png', 'PNG', 'bmp', 'BMP']


class TrainModel:
    model_update = Subject()

    def __init__(self, dir_path):
        TrainModel._ensure_model_dir_valid(dir_path)
        self.dir_path = dir_path

    @property
    def name(self):
        return os.path.basename(self.dir_path)

    @property
    def graph_file_path(self):
        return os.path.join(self.dir_path, KEY_FILE_GRAPH)

    @property
    def labels_file_path(self):
        return os.path.join(self.dir_path, KEY_FILE_LABELS)

    @property
    def summary_file_path(self):
        return os.path.join(self.dir_path, KEY_FILE_SUMMARY)

    @property
    def bottleneck_file_path(self):
        return os.path.join(self.dir_path, KEY_FILE_BOTTLENECK)

    @property
    def thumbnails_file_path(self):
        return os.path.join(self.dir_path, KEY_FILE_THUMBNAILS)

    def thumbnail_file_path_under_label(self, label):
        thumbnail_dir_path = os.path.join(self.thumbnails_file_path, label)
        for thumbnail_candidate in os.listdir(thumbnail_dir_path):
            for ext in IMAGE_EXTENSIONS:
                if thumbnail_candidate.endswith(ext):
                    return os.path.join(thumbnail_dir_path, thumbnail_candidate)
        raise FileNotFoundError("Thumbnail for {} does not exist.".format(self.dir_path))

    def delete(self):
        send2trash(self.dir_path)
        TrainModel._notify_model_update()

    @staticmethod
    def _ensure_model_dir_valid(dir_path):
        entries = os.listdir(dir_path)
        missing_file_names = []
        for file_name in KEY_FILE_NAMES:
            if file_name not in entries:
                missing_file_names.append(file_name)

        if missing_file_names:
            raise ValueError("Directory {} does not contain files: \n\t{}".format(dir_path, missing_file_names))

    @staticmethod
    def _notify_model_update():
        TrainModel.model_update.on_next(TrainModel.load())

    @staticmethod
    def load():
        trained_models_path = absolute_path_of('trained_models')

        entries = os.listdir(trained_models_path)
        abs_entry_paths = [os.path.join(trained_models_path, entry) for entry in entries]
        dir_entry_paths = list(filter(lambda entry_path: os.path.isdir(entry_path), abs_entry_paths))

        models = []
        for dir_entry_path in dir_entry_paths:
            try:
                models.append(TrainModel(dir_entry_path))
            except ValueError as e:
                print(e)

        return models
