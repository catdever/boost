from ..base import StatefulBase
from aiohttp import web
from ..base.types import *


class BaseModel(StatefulBase):
    def __init__(self, lr: float = 10e-3, data_dir: str = '/.cache', **kwargs):
        super().__init__()
        self.lr = lr
        self.data_dir = data_dir

    def post_start(self):
        """ Executes after the process forks """
        pass

    def state(self):
        return dict(lr=self.lr, data_dir=self.data_dir)

    def train(self, query: Query, choices: List[Choice], labels: Labels) -> None:
        """ train """
        raise web.HTTPNotImplemented

    def rank(self, query: Query, choices: List[Choice]) -> Ranks:
        """
        sort list of indices of topk candidates
        """
        raise web.HTTPNotImplemented
