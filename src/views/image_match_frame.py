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

    def _perform_layout(self):
        sizer_root = wx.BoxSizer(wx.VERTICAL)

        self.scroll_content_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.scrolled_panel.SetSizer(self.scroll_content_sizer)

        sizer_root.Add(self.scrolled_panel, 1, wx.EXPAND | wx.ALL, 5)
        sizer_root.Add(self.match_button, 0, wx.EXPAND | wx.ALL, 5)

        self.SetMinSize(self.GetSize())
        self.SetSizer(sizer_root)

        # TODO: Do something with horizontal scrollbar takes up space
        self.scrolled_panel.ShowScrollbars(wx.SHOW_SB_DEFAULT, wx.SHOW_SB_NEVER)
        self.scrolled_panel.SetupScrolling(scroll_y=False)
        self.scrolled_panel.SendSizeEvent()
