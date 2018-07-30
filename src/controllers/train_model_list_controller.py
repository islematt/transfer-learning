import wx

from src.models.train_model import TrainModel
from src.views.train_model_list_frame import TrainModelListFrame
from src.controllers.train_model_controller import TrainModelController


class TrainModelListController:
    def __init__(self):
        self._init_views()
        self._setup_callbacks()
        self._reload_train_models(TrainModel.load())
        self.train_model_list_frame.Show()

    def _init_views(self):
        self.train_model_list_frame = TrainModelListFrame(None)

    def _setup_callbacks(self):
        TrainModel.model_update.subscribe(self._reload_train_models)
        self.train_model_list_frame.list_selection.subscribe(self._toggle_buttons_state)
        self.train_model_list_frame.new.Bind(wx.EVT_BUTTON, self._show_train_model_frame)
        self.train_model_list_frame.delete.Bind(wx.EVT_BUTTON, self._confirm_delete_model)

    def _show_train_model_frame(self, ignored):
        self.train_model_frame = TrainModelController()

    def _confirm_delete_model(self, ignored):
        try:
            dialog = wx.MessageDialog(None, "Are you sure you want to delete this model?", 'HEADS UP!!', wx.YES_NO)
            result = dialog.ShowModal()

            if result == wx.ID_YES:
                self._delete_model()
        finally:
            dialog.Destroy()

    def _delete_model(self):
        selected_idx = self.train_model_list_frame.selected_idx
        if selected_idx < 0:
            return

        model = self.models[selected_idx]
        model.delete()

    def _reload_train_models(self, models):
        self.models = models
        self.train_model_list_frame.show_train_model(models)

    def _toggle_buttons_state(self, selected_item_count):
        if selected_item_count > 0:
            self.train_model_list_frame.select.Enable()
            self.train_model_list_frame.delete.Enable()
        else:
            self.train_model_list_frame.select.Disable()
            self.train_model_list_frame.delete.Disable()
