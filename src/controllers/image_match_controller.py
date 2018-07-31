import logging

import wx

from src.views.image_match_frame import ImageMatchFrame
from src.image_matcher import match

logger = logging.getLogger('app')

# TODO: Change value
THRESHOLD = 0.1
SCROLLBAR_HEIGHT = 30


class ImageMatchController:
    def __init__(self, model):
        self.model = model

        self._init_views()
        self._setup_callbacks()
        self.view.Show()

    def _init_views(self):
        self.view = ImageMatchFrame(None)

    def _setup_callbacks(self):
        self.view.Bind(wx.EVT_BUTTON, self._sample_and_show_matched_images, self.view.match_button)

    def _sample_and_show_matched_images(self, ignored):
        # TODO: Run on thread and show progress
        match_results = match(3, 0, self.model.graph_file_path, self.model.labels_file_path)
        for sampled_file_path, labels, probabilities in match_results:
            if probabilities[0] < THRESHOLD:
                return
            self._show_match_result(sampled_file_path, labels[0])

            msg = '\n'.join(["\t{}: {}".format(label, probability) for label, probability in zip(labels, probabilities)])
            logger.info('\n{}: \n{}'.format(sampled_file_path, msg))

        self.view.Layout()

    def _show_match_result(self, sampled_file_path, label):
        label_thumbnail_path = self.model.thumbnail_file_path_under_label(label)

        panel = wx.Panel(self.view.scrolled_panel, style=wx.SIMPLE_BORDER)

        sampled_static_bitmap = self._load_static_bitmap(panel, sampled_file_path)
        label_static_bitmap = self._load_static_bitmap(panel, label_thumbnail_path)

        self.add_static_bitmap_into_panel(panel, sampled_static_bitmap, label_static_bitmap)

    def add_static_bitmap_into_panel(self, panel, sampled_static_bitmap, label_static_bitmap):
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(sampled_static_bitmap, 0)
        sizer.Add(label_static_bitmap, 0)

        panel.SetSizer(sizer)

        self.view.scroll_content_sizer.Add(panel, flag=wx.ALIGN_CENTER_VERTICAL | wx.BOTTOM, border=SCROLLBAR_HEIGHT)
        self.view.scroll_content_sizer.AddSpacer(20)

    def _load_static_bitmap(self, parent, image_path):
        bitmap = wx.Bitmap(wx.Image(image_path))

        _, scrolled_panel_height = self.view.scrolled_panel.GetSize()
        bitmap_width, bitmap_height = bitmap.GetSize()
        scale = (scrolled_panel_height - SCROLLBAR_HEIGHT) / bitmap_height

        new_size = (int(bitmap_width * scale), int(bitmap_height * scale))
        bitmap.SetSize(new_size)
        return wx.StaticBitmap(parent, wx.ID_ANY, bitmap)
