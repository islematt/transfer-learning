import os
from shutil import rmtree

import wx
from pubsub import pub
from send2trash import send2trash

from src.utils.file_utils import absolute_path_of

KEY_MODEL_MODIFIED = 'MODEL_MODIFIED'

class TrainModel:
    def __init__(self, dir_path):
        self.dir_path = dir_path

    @property
    def name(self):
        return os.path.basename(self.dir_path)

    def delete(self):
        send2trash(self.dir_path)
        pub.sendMessage(KEY_MODEL_MODIFIED)

    @staticmethod
    def load():
        trained_models_path = absolute_path_of('trained_models')

        entries = os.listdir(trained_models_path)
        abs_entry_paths = [os.path.join(trained_models_path, entry) for entry in entries]
        dir_entry_paths = list(filter(lambda entry_path: os.path.isdir(entry_path), abs_entry_paths))
        models = [TrainModel(dir_entry_path) for dir_entry_path in dir_entry_paths]

        return models

class RootFrame(wx.Frame):
    def __init__(self, parent):
        wx.Frame.__init__(self, parent, title="Main View", size=(300, 150))

        self._init_views()
        self._setup_views()
        self.update_buttons_state()

        self._bind_callbacks()
        self._perform_layout()

    def _init_views(self):
        self.list_save_state = wx.ListCtrl(self, id=wx.ID_ANY, style=wx.LC_REPORT|wx.LC_SINGLE_SEL)
        self.new = wx.Button(self, label="New")
        self.select = wx.Button(self, label="Select")
        self.delete = wx.Button(self, label="delete")

    def _setup_views(self):
        self.delete.SetForegroundColour((0, 255, 0))

    def _bind_callbacks(self):
        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.update_buttons_state, self.list_save_state)
        self.Bind(wx.EVT_LIST_ITEM_DESELECTED, self.update_buttons_state, self.list_save_state)

    def _perform_layout(self):
        sizer_root = wx.BoxSizer(wx.HORIZONTAL)
        sizer_buttons = wx.BoxSizer(wx.VERTICAL)

        sizer_buttons.Add(self.new, 0, wx.EXPAND)
        sizer_buttons.Add(self.select, 0, wx.EXPAND)
        sizer_buttons.AddStretchSpacer(1)
        sizer_buttons.Add(self.delete, 0, wx.EXPAND)

        sizer_root.Add(self.list_save_state, 1, wx.EXPAND | wx.ALL, 3)
        sizer_root.Add(sizer_buttons, 0, wx.EXPAND | wx.TOP | wx.RIGHT | wx.BOTTOM, 5)

        self.SetMinSize(self.GetSize())
        self.SetSizer(sizer_root)

    def update_buttons_state(self, ignored=None):
        if self.list_save_state.GetSelectedItemCount() > 0:
            self.select.Enable()
            self.delete.Enable()
        else:
            self.select.Disable()
            self.delete.Disable()

    @property
    def selected_idx(self):
        return self.list_save_state.GetFirstSelected()

    def show_train_model(self, models):
        self.list_save_state.ClearAll()
        self.list_save_state.InsertColumn(0, '#', width = 30)
        self.list_save_state.InsertColumn(1, 'name', width = 100)
        for row_idx in range(len(models)):
            model = models[row_idx]
            self.list_save_state.Append([row_idx, model.name])

class Controller:
    def __init__(self, app):
        self.models = TrainModel.load()

        self.root_frame = RootFrame(None)
        self.root_frame.show_train_model(self.models)
        self.root_frame.delete.Bind(wx.EVT_BUTTON, self.confirm_delete_model)

        pub.subscribe(self.reload_train_models, KEY_MODEL_MODIFIED)

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

if __name__ == "__main__":
    app = wx.App(False)
    controller = Controller(app)
    app.MainLoop()
