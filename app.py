import os

import wx

from src.models.train_model import TrainModel
from src.views.root_frame import RootFrame

class Controller:
    def __init__(self, app):
        self._init_views()
        self._setup_callbacks()
        self._reload_train_models(TrainModel.load())
        self.root_frame.Show()

    def _init_views(self):
        self.root_frame = RootFrame(None)

    def _setup_callbacks(self):
        TrainModel.model_update.subscribe(self._reload_train_models)
        self.root_frame.list_selection.subscribe(self._toggle_buttons_state)
        self.root_frame.delete.Bind(wx.EVT_BUTTON, self._confirm_delete_model)

    def _confirm_delete_model(self, ignored):
        try:
            dialog = wx.MessageDialog(None, "Are you sure you want to delete this model?", 'HEADS UP!!', wx.YES_NO)
            result = dialog.ShowModal()
             
            if result == wx.ID_YES:
                self._delete_model()
        finally:
            dialog.Destroy()

    def _delete_model(self):
        selected_idx = self.root_frame.selected_idx
        if selected_idx < 0:
            return

        model = self.models[selected_idx]
        model.delete()

    def _reload_train_models(self, models):
        self.models = models
        self.root_frame.show_train_model(models)

    def _toggle_buttons_state(self, selected_item_count):
        if selected_item_count > 0:
            self.root_frame.select.Enable()
            self.root_frame.delete.Enable()
        else:
            self.root_frame.select.Disable()
            self.root_frame.delete.Disable()


if __name__ == "__main__":
    app = wx.App(False)
    controller = Controller(app)
    app.MainLoop()
