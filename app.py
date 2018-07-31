import wx

from src.utils import log_utils
from src.controllers.train_model_list_controller import TrainModelListController


if __name__ == "__main__":
    log_utils.setup_logging()
    log_utils.bridge_tf_log()

    app = wx.App(False)
    controller = TrainModelListController()
    app.MainLoop()
