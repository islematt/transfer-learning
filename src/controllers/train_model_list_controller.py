import wx

from src.models.train_model import TrainModel
from src.views.train_model_list_frame import TrainModelListFrame
from src.controllers.train_model_controller import TrainModelController
from src.controllers.image_match_controller import ImageMatchController
from src.utils.wx_utils import show_confirm_dialog


class TrainModelListController:
    def __init__(self):
        self._init_views()
        self._setup_callbacks()
        self._reload_train_models(TrainModel.load())
        self.train_model_list_frame.Show()

    def _init_views(self):
        self.train_model_list_frame = TrainModelListFrame(None)

    def _setup_callbacks(self):
        # TODO: Reload when training finished(or watch file system change)
        TrainModel.model_update.subscribe(self._reload_train_models)
        self.train_model_list_frame.list_selection.subscribe(self._list_selection_changed)
        self.train_model_list_frame.list_activation.subscribe(self._list_activated)
        self.train_model_list_frame.new.Bind(wx.EVT_BUTTON, self._show_train_model_controller)
        self.train_model_list_frame.select.Bind(wx.EVT_BUTTON, self._show_image_match_controller)
        self.train_model_list_frame.delete.Bind(wx.EVT_BUTTON, self._confirm_delete_model)
        # XXX: Remove before release
        self.train_model_list_frame.debug.Bind(wx.EVT_BUTTON, self._debug)

    def _show_train_model_controller(self, ignored=None):
        self.train_model_frame = TrainModelController()

    def _show_image_match_controller(self, ignored=None):
        idx = self.train_model_list_frame.selected_idx
        if idx < 0:
            return
        self.image_model_list = ImageMatchController(self.models[idx])

    def _confirm_delete_model(self, ignored=None):
        show_confirm_dialog(self._delete_model, "Are you sure you want to delete this model?", "HEADS UP!!")

    def _delete_model(self):
        selected_idx = self.train_model_list_frame.selected_idx
        if selected_idx < 0:
            return

        model = self.models[selected_idx]
        model.delete()

    def _reload_train_models(self, models):
        self.models = models
        self.train_model_list_frame.show_train_model(models)

    def _list_selection_changed(self, selected_item_count):
        enable = selected_item_count > 0
        self.train_model_list_frame.select.Enable(enable=enable)
        self.train_model_list_frame.delete.Enable(enable=enable)

    def _list_activated(self, ignored):
        self._show_image_match_controller()

    # noinspection PyMethodMayBeStatic
    def _debug(self, ignored):
        import psutil

        current_process = psutil.Process()
        children = current_process.children(recursive=True)
        for child in children:
            print('Child pid is {}'.format(child.pid))
            print(child.is_running())
            child.terminate()
            print(child.is_running())
