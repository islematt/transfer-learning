import wx
from rx.subjects import Subject


class TrainModelListFrame(wx.Frame):
    def __init__(self, parent):
        wx.Frame.__init__(self, parent, title="Main View", size=(300, 150))
        self.list_selection = Subject()
        self.list_activation = Subject()

        self._init_views()
        self._setup_views()
        self._notify_list_state_changed()

        self._setup_callbacks()
        self._perform_layout()

    def _init_views(self):
        self.list_save_state = wx.ListCtrl(self, id=wx.ID_ANY, style=wx.LC_REPORT|wx.LC_SINGLE_SEL)
        self.new = wx.Button(self, label="New")
        self.select = wx.Button(self, label="Select")
        self.delete = wx.Button(self, label="delete")

    def _setup_views(self):
        self.delete.SetForegroundColour((0, 255, 0))

    def _setup_callbacks(self):
        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self._notify_list_state_changed, self.list_save_state)
        self.Bind(wx.EVT_LIST_ITEM_DESELECTED, self._notify_list_state_changed, self.list_save_state)
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self._notify_list_item_activated, self.list_save_state)

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

    def _notify_list_state_changed(self, ignored=None):
        self.list_selection.on_next(self.list_save_state.GetSelectedItemCount())

    def _notify_list_item_activated(self, ignored):
        self.list_activation.on_next(self.selected_idx)

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

        self._notify_list_state_changed()
