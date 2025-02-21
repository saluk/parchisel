from nicegui import ui

class NotifyException(Exception):
    def __init__(self, msg):
        ui.notify(msg, type="warning")
        super().__init__(msg)