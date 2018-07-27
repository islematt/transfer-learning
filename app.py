import os

import wx
from pubsub import pub

from src.models.train_model import TrainModel, KEY_MODEL_MODIFIED
from src.views.root_frame import RootFrame, KEY_LIST_STATE_CHANGED

class Controller:
    def __init__(self, app):
        self.models = TrainModel.load()

        self.root_frame = RootFrame(None)
        self.root_frame.show_train_model(self.models)
        self.root_frame.delete.Bind(wx.EVT_BUTTON, self.confirm_delete_model)

        pub.subscribe(self.reload_train_models, KEY_MODEL_MODIFIED)
        pub.subscribe(self.toggle_buttons_state, KEY_LIST_STATE_CHANGED)

        self.root_frame.Show()

    def confirm_delete_model(self, ignored):
        try:
            dlg = wx.MessageDialog(None, "Are you sure you want to delete this model?", 'HEADS UP!!', wx.YES_NO)
            result = dlg.ShowModal()
             
            if result == wx.ID_YES:
                self.delete_model()
        finally:
            dlg.Destroy()

    def delete_model(self):
        selected_idx = self.root_frame.selected_idx
        if selected_idx < 0:
            return

        model = self.models[selected_idx]
        model.delete()

    def reload_train_models(self):
        self.models = TrainModel.load()
        self.root_frame.show_train_model(self.models)

    def toggle_buttons_state(self):
        if self.root_frame.list_save_state.GetSelectedItemCount() > 0:
            self.root_frame.select.Enable()
            self.root_frame.delete.Enable()
        else:
            self.root_frame.select.Disable()
            self.root_frame.delete.Disable()

if __name__ == "__main__":
    app = wx.App(False)
    controller = Controller(app)
    app.MainLoop()
