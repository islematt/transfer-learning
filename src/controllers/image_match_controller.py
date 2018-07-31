from src.views.image_match_frame import ImageMatchFrame


class ImageMatchController:
    def __init__(self, model):
        self.model = model
        print(model.dir_path)

        self._init_views()
        self.view.Show()

    def _init_views(self):
        self.view = ImageMatchFrame(None)
