from nicegui import ui

import traceback

class NotifyException(Exception):
    def __init__(self, msg=""):
        ui.notify(msg, type="warning")
        traceback.print_exc()
        super().__init__(msg)