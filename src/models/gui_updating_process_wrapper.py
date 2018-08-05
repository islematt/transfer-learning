import threading
import multiprocessing as mp
from multiprocessing import Queue
import logging
from abc import ABC, abstractmethod

logger = logging.getLogger('app')


def raise_if_not_callable(arg):
    if not callable(arg):
        raise ValueError("{} is not callable".format(arg))


class GuiUpdatingProcessWrapper(ABC):
    def __init__(self):
        self._process = None
        self._gui_update_thread = None
        self.event_queue = Queue()

    def start(self):
        if self.is_training:
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
            self._gui_update_thread = None

        if self._process:
            self._process.terminate()
            self._process = None

    @property
    def is_training(self):
        return (self._process and self._process.is_alive()) or\
               (self._gui_update_thread and self._gui_update_thread.is_alive())

    @property
    @abstractmethod
    def name(self):
        pass

    @abstractmethod
    def _process_body(self):
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
        self.body()
        self.event_queue.put(None)
