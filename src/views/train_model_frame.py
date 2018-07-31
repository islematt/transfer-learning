import wx

ID_INPUT_SELECT = 1000
ID_OUTPUT_SELECT = 2000
ID_INPUT_TEXT_CTRL = 1001
ID_OUTPUT_TEXT_CTRL = 2001


class TrainModelFrame(wx.Frame):
    def __init__(self, parent):
        wx.Frame.__init__(self, parent, title="Train Model", size=(500, 350))

        self._init_views()
        self._perform_layout()

    def _init_views(self):
        self.input_label = wx.StaticText(self, label="Input")
        self.input_dir_ctrl = wx.TextCtrl(self, id=ID_INPUT_TEXT_CTRL, style=wx.TE_READONLY)
        self.input_select = wx.Button(self, id=ID_INPUT_SELECT, label="Open")

        self.output_label = wx.StaticText(self, label="Output")
        self.output_dir_ctrl = wx.TextCtrl(self, id=ID_OUTPUT_TEXT_CTRL, style=wx.TE_READONLY)
        self.output_select = wx.Button(self, id=ID_OUTPUT_SELECT, label="Open")

        self.train_button = wx.Button(self, label="Train")

        self.progress_bar = wx.Gauge(self, range=100, style=wx.GA_HORIZONTAL)

        self.log_ctrl = wx.TextCtrl(self, style=wx.TE_READONLY | wx.TE_MULTILINE)

    def _perform_layout(self):
        sizer_root = wx.BoxSizer(wx.VERTICAL)
        grid_sizer = wx.FlexGridSizer(rows=2, cols=3, hgap=5, vgap=5)

        grid_sizer.Add(self.input_label)
        grid_sizer.Add(self.input_dir_ctrl, 1, wx.EXPAND)
        grid_sizer.Add(self.input_select)

        grid_sizer.Add(self.output_label)
        grid_sizer.Add(self.output_dir_ctrl, 1, wx.EXPAND)
        grid_sizer.Add(self.output_select)

        grid_sizer.AddGrowableCol(1)

        sizer_root.Add(grid_sizer, 0, wx.EXPAND | wx.ALL, 5)
        sizer_root.Add(self.train_button, 0, wx.EXPAND | wx.ALL, 5)
        sizer_root.Add(self.progress_bar, 0, wx.EXPAND | wx.ALL, 5)
        sizer_root.Add(self.log_ctrl, 1, wx.EXPAND | wx.ALL, 5)

        self.SetSizer(sizer_root)
