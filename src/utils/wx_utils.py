import wx


def show_confirm_dialog(body, message, caption):
    dialog = None
    try:
        dialog = wx.MessageDialog(None, message, caption, wx.YES_NO)
        result = dialog.ShowModal()

        if result == wx.ID_YES:
            body()
    finally:
        if dialog:
            dialog.Destroy()
