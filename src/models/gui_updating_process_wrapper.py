import threading
import multiprocessing as mp
from multiprocessing import Queue
import logging
from abc import ABC, abstractmethod

import wx

from src.utils.function_utils import raise_if_not_callable

logger = logging.getLogger('app')


class Event:
    pass


class GuiEvent(Event):
    pass


class ProgressEvent(GuiEvent):
    def __init__(self, progress):
        self.progress = progress


class LogEvent(GuiEvent):
    def __init__(self, message):
        self.message = message


class GuiUpdatingProcessWrapper(ABC):
    def __init__(self):
        self._process = None
        self._gui_update_thread = None
        self.event_queue = Queue()

    def start(self):
        if self.is_alive:
            self.terminate()
        self._prepare()

        self._gui_update_thread = GuiUpdateThread(event_queue=self.event_queue,
                                                  gui_update_callback=self._gui_update_callback,
                                                  name=self.name)
        self._gui_update_thread.start()
        self._process = Process(event_queue=self.event_queue, body=self._process_body)
        self._process.start()

    def post_event(self, event):
        self._gui_update_thread.post_event(event)

    def terminate(self):
        self._clean_up()
        if self._gui_update_thread:
            self._gui_update_thread.terminate()

        if self._process:
            self._process.terminate()
            self._process.join()

            # DO NOT REMOVE LINES BELOW
            # Waiting a little while / calling Process.is_alive() might has effect on non-terminating process problem.
            # import time
            # time.sleep(0.2)
            logger.debug("{} / {} / {}".format(self._process, self._process.is_alive(), self._process.exitcode))

    @property
    def is_alive(self):
        return (self._process and self._process.is_alive()) or\
               (self._gui_update_thread and self._gui_update_thread.is_alive())

    @property
    @abstractmethod
    def name(self):
        pass

    @abstractmethod
    def _process_body(self) -> Event:
        pass

    @abstractmethod
    def _gui_update_callback(self, event):
        pass

    @abstractmethod
    def _prepare(self):
        pass

    @abstractmethod
    def _clean_up(self):
        pass


class GuiUpdateThread(threading.Thread):
    def __init__(self, *args, **kwargs):
        event_queue = kwargs.pop('event_queue', None)
        gui_update_callback = kwargs.pop('gui_update_callback', None)
        name = kwargs.pop('name', 'GuiUpdateThread')
        raise_if_not_callable(gui_update_callback)

        super(GuiUpdateThread, self).__init__(*args, **kwargs)
        self.event_queue = event_queue
        self.gui_update_callback = gui_update_callback
        self.name = name

    def run(self):
        while True:
            event = self.event_queue.get()
            if not event:
                break

            if isinstance(event, GuiEvent):
                wx.CallAfter(self.gui_update_callback, event)
            else:
                self.gui_update_callback(event)

        logger.debug('Stopped {}'.format(self.name))

    def post_event(self, event):
        self.event_queue.put(event)

    def terminate(self):
        self.post_event(None)


class Process(mp.Process):
    def __init__(self, *args, **kwargs):
        event_queue = kwargs.pop('event_queue', None)
        body = kwargs.pop('body', None)
        raise_if_not_callable(body)

        super(Process, self).__init__(*args, **kwargs)
        self.event_queue = event_queue
        self.body = body

    def run(self):
        try:
            result_event = self.body()

            self.event_queue.put(result_event)
            self.event_queue.put(None)
        except Exception as e:
            logger.debug(str(e))
