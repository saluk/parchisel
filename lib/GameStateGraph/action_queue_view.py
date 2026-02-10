from nicegui import ui
from .model.game_state import GameState


class ActionQueueView:
    def __init__(self, game_state: GameState):
        self.game_state = game_state

    def refresh(self):
        self.build.refresh()

    async def build(self):
        with ui.card():
            with ui.list():
                for action in self.game_state.operation_stack:
                    action
