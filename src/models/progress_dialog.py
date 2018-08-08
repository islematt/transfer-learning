import threading
from multiprocessing import Queue

import wx

from src.utils.function_utils import raise_if_not_callable, noop


class ProgressDialogEvent:
    def __init__(self, progress):
        self.progress = progress


class ProgressDialog(threading.Thread):
    def __init__(self, *args, **kwargs):
        max_progress = kwargs.pop('max_progress', None)
        cancel_callback = kwargs.pop('cancel_callback', noop)
        raise_if_not_callable(cancel_callback)

        super(ProgressDialog, self).__init__(*args, **kwargs)
        self._dialog = None
        self._max_progress = max_progress
        self._event_queue = Queue()
        self._cancel_callback = cancel_callback

    def run(self):
        while True:
            event = self._event_queue.get()
            cancelled = self._dialog.WasCancelled()

            if cancelled:
                wx.CallAfter(self._cancel_callback)
                break
            if not event or event.progress >= self._max_progress:
                break

            wx.CallAfter(self._dialog.Update, event.progress)
        wx.CallAfter(self._dialog.Destroy)

    def show(self):
        self._dialog = wx.ProgressDialog("A progress box", "Time remaining", self._max_progress,
                                         style=wx.PD_CAN_ABORT | wx.PD_ELAPSED_TIME | wx.PD_REMAINING_TIME)
        self.start()

    def hide(self):
        # TODO: Cancel task
        self._event_queue.put(None)

    def update(self, progress):
        self._event_queue.put(ProgressDialogEvent(progress))
