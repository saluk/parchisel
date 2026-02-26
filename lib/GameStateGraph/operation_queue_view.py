from nicegui import ui

from lib.base_components.small_button import SmallButton
from .model.game_state import GameState


class OperationQueueView:
    def __init__(self, state_view, game_state: GameState):
        self.state_view = state_view
        self.game_state = game_state

    def refresh(self):
        self.build.refresh()

    async def remove_operation(self, index):
        self.game_state.operation_queue.remove(index, self.game_state)
        self.state_view.refresh()

    @ui.refreshable
    async def build(self):
        with ui.card():
            with ui.list():
                # TODO shouldn't call .queue directly
                if not self.game_state.operation_queue.queue:
                    ui.label("(No operations performed yet)")
                    return
                with ui.scroll_area().classes(f"w-100 h-150 border") as scroll_area:
                    for i, operation in enumerate(
                        self.game_state.operation_queue.queue
                    ):
                        with ui.item():

                            async def d(i=i):
                                await self.remove_operation(i)

                            SmallButton("x", on_click=d)
                            ui.label(
                                f"{i} - "
                                + operation.get_string(self.game_state.current_state)
                                + (
                                    f" {operation.recent_run.traceback} "
                                    if operation.recent_run
                                    and operation.recent_run.traceback
                                    else ""
                                )
                            ).classes(
                                "text-negative"
                                if operation.recently_successful == False
                                else (
                                    "text-positive"
                                    if operation.recently_successful == True
                                    else ""
                                )
                            )

                            async def move_up(i=i):
                                self.game_state.operation_queue.move_up(
                                    i, self.game_state
                                )
                                self.state_view.refresh()

                            async def move_down(i=i):
                                self.game_state.operation_queue.move_down(
                                    i, self.game_state
                                )
                                self.state_view.refresh()

                            if i > 0:
                                SmallButton("^", on_click=move_up)
                            if i < len(self.game_state.operation_queue.queue) - 1:
                                SmallButton("v", on_click=move_down)
                    scroll_area.scroll_to(percent=100)
