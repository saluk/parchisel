from nicegui import ui
from .model.game_state import GameState


class OperationQueueView:
    def __init__(self, game_state: GameState):
        self.game_state = game_state

    def refresh(self):
        self.build.refresh()

    async def build(self):
        with ui.card():
            with ui.list():
                for operation in self.game_state.operation_stack:
                    ui.item(str(operation))
