import wx
from wx.lib.scrolledpanel import ScrolledPanel


class ImageMatchFrame(wx.Frame):
    def __init__(self, parent):
        wx.Frame.__init__(self, parent, title="Train Model", size=(800, 500))

        self._init_views()
        self._perform_layout()

    def _init_views(self):
        self.scrolled_panel = ScrolledPanel(self, style=wx.SIMPLE_BORDER)
        self.match_button = wx.Button(self, label="Match")

        self.buttons = []
        for i in range(30):
            btn = wx.Button(self.scrolled_panel, label="aaaa" + str(i))
            self.buttons.append(btn)

    def _perform_layout(self):
        sizer_root = wx.BoxSizer(wx.VERTICAL)

        inner_sizer = wx.BoxSizer(wx.HORIZONTAL)

        for button in self.buttons:
            inner_sizer.Add(button)

        self.scrolled_panel.SetSizer(inner_sizer)

        sizer_root.Add(self.scrolled_panel, 1, wx.EXPAND | wx.ALL, 5)
        sizer_root.Add(self.match_button, 0, wx.EXPAND | wx.ALL, 5)

        self.SetSizer(sizer_root)

        self.scrolled_panel.ShowScrollbars(wx.SHOW_SB_DEFAULT, wx.SHOW_SB_NEVER)
        self.scrolled_panel.SetupScrolling()
        self.scrolled_panel.SendSizeEvent()
