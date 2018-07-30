import os
import threading

import wx
from rx.subjects import BehaviorSubject

from src.retrain import retrain, search_image_progress, cache_bottleneck_progress, training_progress, cleanup_progress
from src.views.train_model_frame import TrainModelFrame, ID_INPUT_SELECT
from src.utils import log_utils
from src.utils.file_utils import get_root_dir


class TrainOptions:
    def __init__(self):
        self._image_dir = ''
        self._base_output_dir = ''
        self.update = BehaviorSubject(self)

    @property
    def image_dir(self):
        return self._image_dir

    @property
    def base_output_dir(self):
        return self._base_output_dir

    @image_dir.setter
    def image_dir(self, path):
        self._image_dir = path
        self.update.on_next(self)

    @base_output_dir.setter
    def base_output_dir(self, path):
        self._base_output_dir = path
        self.update.on_next(self)

    def are_enough_for_training(self):
        return self._image_dir != '' and \
               self._base_output_dir != ''


class TrainThread(threading.Thread):
    def __init__(self, *args, **kwargs):
        self.train_options = kwargs.pop('train_options', None)
        self.pre_callback = kwargs.pop('pre_callback', None)
        self.post_callback = kwargs.pop('post_callback', None)
        super(TrainThread, self).__init__(*args, **kwargs)

    def run(self):
        def config(FLAGS):
            root_dir = get_root_dir()

            base_output_dir = os.path.join(root_dir, self.train_options.base_output_dir)

            FLAGS.image_dir = os.path.join(root_dir, self.train_options.image_dir)
            FLAGS.output_graph = os.path.join(base_output_dir, 'graph.pb')
            FLAGS.output_labels = os.path.join(base_output_dir, 'labels.txt')
            FLAGS.summaries_dir = os.path.join(base_output_dir, 'summary')
            FLAGS.bottleneck_dir = os.path.join(base_output_dir, 'bottleneck')

            FLAGS.how_many_training_steps = 10

            return FLAGS

        if self.pre_callback:
            self.pre_callback()

        retrain(config)

        if self.post_callback:
            self.post_callback()


class TrainModelController:
    def __init__(self):
        self.train_options = TrainOptions()
        self._init_views()
        self._setup_callbacks()
        self.view.Show()

    def _init_views(self):
        self.view = TrainModelFrame(None)

    def _setup_callbacks(self):
        self.view.Bind(wx.EVT_BUTTON, self._select_directory, self.view.input_select)
        self.view.Bind(wx.EVT_BUTTON, self._select_directory, self.view.output_select)
        self.view.Bind(wx.EVT_BUTTON, self._start_training, self.view.train_button)

        self.train_options.update.subscribe(self._on_train_option_update)

    def _on_train_option_update(self, options):
        self.view.input_dir_ctrl.SetValue(options.image_dir)
        self.view.output_dir_ctrl.SetValue(options.base_output_dir)
        self.view.train_button.Enable(enable=options.are_enough_for_training())

    def _select_directory(self, event):
        dir_dialog = wx.DirDialog(self.view, message="message", name="name")
        dir_dialog.ShowModal()

        path = dir_dialog.GetPath()
        self._update_train_options(event, path)

        dir_dialog.Destroy()

    def _update_train_options(self, event, path):
        if event.GetId() == ID_INPUT_SELECT:
            self.train_options.image_dir = path
        else:
            self.train_options.base_output_dir = path

    def _start_training(self, ignored=None):
        def update_progress_bar(progress, start, end):
            proportion = end - start
            p = start + (progress[0] / progress[1]) * proportion
            p = int(p * 100)

            wx.CallAfter(self.view.progress_bar.SetValue, p)

        def gui_log_output(message):
            wx.CallAfter(self.view.log_ctrl.AppendText, message + '\n')

        def pre_train_callback():
            self.view.train_button.Disable()
            log_utils.redirect_console_to(gui_log_output)

        def post_train_callback():
            # TODO: Change 'Train' button into 'Next' button
            log_utils.redirect_console_to(None)

        search_image_progress.subscribe(lambda p: update_progress_bar(p, 0.0, 0.1))
        cache_bottleneck_progress.subscribe(lambda p: update_progress_bar(p, 0.1, 0.5))
        training_progress.subscribe(lambda p: update_progress_bar(p, 0.5, 0.9))
        cleanup_progress.subscribe(lambda p: update_progress_bar(p, 0.9, 1.0))

        t = TrainThread(train_options=self.train_options,
                        pre_callback=pre_train_callback,
                        post_callback=post_train_callback)
        t.start()
