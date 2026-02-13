from . import operation_base


class OperationQueue:
    def __init__(self):
        self.queue: list[operation_base.OperationBase] = []

    def add(self, operation: operation_base.OperationBase, game_state):
        self.queue.append(operation)

    def remove(self, index: int, game_state):
        del self.queue[index]
        self.replay(game_state)

    def replay(self, game_state):
        state = game_state.initial_state.copy()
        for operation in self.queue:
            operation.replay(state)
        game_state.current_state = state
