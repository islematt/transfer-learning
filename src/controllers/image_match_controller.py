import logging
import weakref

import wx

from src.models.gui_updating_process_wrapper import GuiUpdatingProcessWrapper, Event, GuiEvent, ProgressEvent, LogEvent
from src.views.image_match_frame import ImageMatchFrame
from src.image_matcher import match, progress_observable
from src.utils.function_utils import noop
from src.utils.wx_utils import show_confirm_dialog
from src.utils.requests_utils import Session

logger = logging.getLogger('app')

# TODO: Change value
THRESHOLD = 0.1
SCROLLBAR_HEIGHT = 30


class ImageMatchController:
    def __init__(self, model):
        self._init_models(model)
        self._init_views()
        self._setup_callbacks()
        self.view.Show()

    def _init_models(self, model):
        self.model = model
        self.matcher = None

    def _init_views(self):
        self.view = ImageMatchFrame(None)

    def _setup_callbacks(self):
        self.view.Bind(wx.EVT_BUTTON, self._sample_and_show_matched_images, self.view.match_button)
        self.view.Bind(wx.EVT_CLOSE, self._clean_up_and_close)

    def _sample_and_show_matched_images(self, ignored):
        self.matcher = Matcher(self.view, self.model)
        self.matcher.start()

    def _clean_up_and_close(self, ignored):
        def do_clean_up_and_close():
            self.matcher.terminate() if self.matcher else noop
            self.view.Destroy()

        if not self.matcher or not self.matcher.is_alive:
            do_clean_up_and_close()
            return

        show_confirm_dialog(do_clean_up_and_close, "", "Stop matching?")


class MatchResultEvent(GuiEvent):
    def __init__(self, match_results):
        self.match_results = match_results


class Matcher(GuiUpdatingProcessWrapper):
    def __init__(self, view, model):
        super(Matcher, self).__init__()
        self.disposable = None
        self.view_ref = weakref.ref(view)
        self.model_ref = weakref.ref(model)

    @property
    def name(self):
        return 'Image matcher'

    @property
    def view(self):
        return self.view_ref()

    @property
    def model(self):
        return self.model_ref()

    def _process_body(self) -> Event:
        if not self.model:
            return MatchResultEvent(None)

        match_results = match(1, 0, self.model.graph_file_path, self.model.labels_file_path)
        return MatchResultEvent(match_results)

    def _gui_update_callback(self, event):
        if not self.view or not self.model:
            return

        if isinstance(event, ProgressEvent):
            self.view.progress_bar.SetValue(event.progress)
        if isinstance(event, MatchResultEvent) and event.match_results:
            self._show_match_results(event.match_results)
            self.view.Layout()

    def _prepare(self):
        if not self.view:
            return

        wx.CallAfter(self.view.match_button.Disable)
        self.disposable = progress_observable.subscribe(lambda p: self.post_event(ProgressEvent(p)))
        session = Session.create()
        session.trust_env = False

    def _clean_up(self):
        wx.CallAfter(self.view.match_button.Enable)
        self.disposable.dispose()
        Session.dispose()

        logger.debug("Cleaning up training...")

    def _show_match_results(self, match_results):
        for sampled_file_path, labels, probabilities in match_results:
            if probabilities[0] < THRESHOLD:
                return
            self._show_match_result(sampled_file_path, labels[0])

            msg = '\n'.join(["\t{}: {}".format(label, probability) for label, probability in zip(labels, probabilities)])
            logger.debug('\n{}: \n{}'.format(sampled_file_path, msg))

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
