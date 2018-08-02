import os
import threading
import multiprocessing as mp
from multiprocessing import Queue
import shutil
import weakref
import logging

import wx
from rx.subjects import BehaviorSubject
from send2trash import send2trash

from src.retrain import retrain, search_image_progress, cache_bottleneck_progress, training_progress, cleanup_progress
from src.views.train_model_frame import TrainModelFrame, ID_INPUT_SELECT
from src.utils import log_utils
from src.utils.file_utils import get_root_dir
from src.utils.sort_utils import natural_keys
from src.utils.function_utils import foreach
from src.utils.wx_utils import show_confirm_dialog
from src.models.train_model import \
    KEY_FILE_GRAPH, KEY_FILE_BOTTLENECK, KEY_FILE_LABELS, KEY_FILE_SUMMARY, KEY_FILE_THUMBNAILS

logger = logging.getLogger('app')


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


class ProgressEvent:
    def __init__(self, progress):
        self.progress = progress


class LogEvent:
    def __init__(self, message):
        self.message = message


class GuiUpdateThread(threading.Thread):
    def __init__(self, progress_bar, log_ctrl):
        super(GuiUpdateThread, self).__init__()
        self.event_queue = Queue()
        self.progress_bar_ref = weakref.ref(progress_bar)
        self.log_ctrl_ref = weakref.ref(log_ctrl)

    def run(self):
        while True:
            event = self.event_queue.get()
            progress_bar = self.progress_bar_ref()
            log_ctrl = self.log_ctrl_ref()
            if not event or not progress_bar or not log_ctrl:
                break

            if isinstance(event, ProgressEvent):
                wx.CallAfter(progress_bar.SetValue, event.progress)
            if isinstance(event, LogEvent):
                wx.CallAfter(log_ctrl.AppendText, event.message + '\n')

        logger.debug('Stopped GuiUpdateThread')

    def update_progress(self, progress):
        self.event_queue.put(ProgressEvent(progress))

    def append_log(self, message):
        self.event_queue.put(LogEvent(message))

    def terminate(self):
        self.event_queue.put(None)


class TrainProcess(mp.Process):
    def __init__(self, *args, **kwargs):
        self.train_options = kwargs.pop('train_options', None)
        super(TrainProcess, self).__init__(*args, **kwargs)

    def run(self):
        def config(FLAGS):
            root_dir = get_root_dir()
            base_output_dir = os.path.join(root_dir, self.train_options.base_output_dir)

            FLAGS.image_dir = os.path.join(root_dir, self.train_options.image_dir)
            FLAGS.output_graph = os.path.join(base_output_dir, KEY_FILE_GRAPH)
            FLAGS.output_labels = os.path.join(base_output_dir, KEY_FILE_LABELS)
            FLAGS.summaries_dir = os.path.join(base_output_dir, KEY_FILE_SUMMARY)
            FLAGS.bottleneck_dir = os.path.join(base_output_dir, KEY_FILE_BOTTLENECK)

            # TODO: Config
            FLAGS.how_many_training_steps = 10

            return FLAGS

        intermediates = retrain(config)
        self.copy_each_first_image(intermediates)

    def copy_each_first_image(self, intermediates):
        base_output_dir = os.path.join(get_root_dir(), self.train_options.base_output_dir)

        image_lists = intermediates['image_lists']
        for label, images in image_lists.items():
            first_image_path = sorted(images['all'], key=natural_keys)[0]
            image_name = os.path.basename(first_image_path)
            out_dir_path = os.path.join(base_output_dir, KEY_FILE_THUMBNAILS, label)

            if os.path.isdir(out_dir_path):
                send2trash(out_dir_path)
            os.makedirs(out_dir_path)

            out_image_path = os.path.join(out_dir_path, image_name)
            shutil.copyfile(first_image_path, out_image_path)


class TrainModelController:
    def __init__(self):
        self.train_options = TrainOptions()
        self.train_process = None
        self.gui_update_thread = None
        self.disposals = None

        self._init_views()
        self._setup_callbacks()
        self.view.Show()

    def _init_views(self):
        self.view = TrainModelFrame(None)

    def _setup_callbacks(self):
        self.view.Bind(wx.EVT_BUTTON, self._select_directory, self.view.input_select)
        self.view.Bind(wx.EVT_BUTTON, self._select_directory, self.view.output_select)
        self.view.Bind(wx.EVT_BUTTON, self._start_training, self.view.train_button)
        self.view.Bind(wx.EVT_CLOSE, self._clean_up_and_close)

        self.train_options.update.subscribe(self._on_train_option_update)

    def _on_train_option_update(self, options):
        self.view.input_dir_ctrl.SetValue(options.image_dir)
        self.view.output_dir_ctrl.SetValue(options.base_output_dir)
        self.view.train_button.Enable(enable=options.are_enough_for_training())

    def _select_directory(self, event):
        message = 'Select image directory' if event.GetId() == ID_INPUT_SELECT else 'Select output directory'
        dir_dialog = wx.DirDialog(self.view, message=message, name="name")
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
        self._clean_up_train()
        self._prepare_train()

        self.gui_update_thread = GuiUpdateThread(self.view.progress_bar, self.view.log_ctrl)
        self.gui_update_thread.start()
        self.train_process = TrainProcess(train_options=self.train_options)
        self.train_process.start()

    def _gui_log_output(self, message):
        self.gui_update_thread.append_log(message)

    def _subscribe_train_progress(self):
        def _update_progress_bar(progress, start, end):
            proportion = end - start
            p = start + (progress[0] / progress[1]) * proportion
            p = int(p * 100)
            self.gui_update_thread.update_progress(p)

        self.disposals = search_image_progress.subscribe(lambda p: _update_progress_bar(p, 0.0, 0.1)), \
            cache_bottleneck_progress.subscribe(lambda p: _update_progress_bar(p, 0.1, 0.5)), \
            training_progress.subscribe(lambda p: _update_progress_bar(p, 0.5, 0.9)), \
            cleanup_progress.subscribe(lambda p: _update_progress_bar(p, 0.9, 1.0))

    def _prepare_train(self):
        wx.CallAfter(self.view.train_button.Disable)
        log_utils.redirect_console_to(self._gui_log_output)
        self._subscribe_train_progress()

    def _clean_up_train(self):
        # TODO: Change 'Train' button into 'Next' button
        log_utils.redirect_console_to(None)
        self._dispose_subscriptions()
        self._stop_train_process()
        self._stop_gui_update_thread()
        logger.debug("Cleaning up training...")

    def _stop_train_process(self):
        if self.train_process:
            self.train_process.terminate()
            self.train_process = None

    def _stop_gui_update_thread(self):
        if self.gui_update_thread:
            self.gui_update_thread.terminate()
            self.gui_update_thread = None

    def _dispose_subscriptions(self):
        if not self.disposals:
            return
        foreach(lambda disposable: disposable.dispose(), self.disposals)
        self.disposals = None

    def _clean_up_and_close(self, ignored):
        show_confirm_dialog(lambda: self._clean_up_train() or self.view.Destroy(), "", "Stop training?")
