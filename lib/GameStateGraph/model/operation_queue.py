from . import operation_base


class OperationQueuex:
    def __init__(self):
        self.queue: list[operation_base.OperationBase] = []


OperationQueue = list
