from nicegui import ui
from .model.game_state import GameState


class OperationQueueView:
    def __init__(self, state_view, game_state: GameState):
        self.state_view = state_view
        self.game_state = game_state

    def refresh(self):
        self.build.refresh()

    async def remove_operation(self, index):
        ui.notify(f"Delete action {index}")
        self.game_state.operation_queue.remove(index, self.game_state)
        self.state_view.refresh()

    @ui.refreshable
    async def build(self):
        with ui.card():
            with ui.list():
                # TODO shouldn't call .queue directly
                if not self.game_state.operation_queue.queue:
                    ui.label("(No operations performed yet)")
                for i, operation in enumerate(self.game_state.operation_queue.queue):
                    with ui.item():

                        async def d(i=i):
                            await self.remove_operation(i)

                        ui.button("x", on_click=d)
                        ui.label(
                            f"{i} - "
                            + operation.get_string(self.game_state.current_state)
                        )
