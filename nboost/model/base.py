from ..base import StatefulBase
from aiohttp import web
from ..base.types import *
from .helpers import download_model, extract
from . import MODEL_PATHS
import os


class BaseModel(StatefulBase):
    def __init__(self,
                 lr: float = 10e-3,
                 model_ckpt: str ='./marco_bert',
                 data_dir: str = './.cache',
                 max_seq_len: int = 128,
                 batch_size: int = 4, **kwargs):
        super().__init__()
        self.lr = lr
        self.data_dir = data_dir
        self.model_ckpt = model_ckpt
        self.model_dir = os.path.dirname(self.model_ckpt)
        self.max_seq_len = max_seq_len
        self.batch_size = batch_size

        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
        if not os.path.exists(self.model_dir) and self.model_ckpt in MODEL_PATHS:
            self.model_ckpt = os.path.join(self.data_dir, MODEL_PATHS[self.model_ckpt]['ckpt'])
            self.model_dir = os.path.dirname(self.model_ckpt)
            if not os.path.exists(self.model_dir):
                file = download_model(self.model_ckpt, self.data_dir)
                extract(file, self.data_dir)
                os.remove(file)
                assert os.path.exists(self.model_dir)
        else:
            raise FileNotFoundError(self.model_ckpt)


    def post_start(self):
        """ Executes after the process forks """
        pass

    def state(self):
        return dict(lr=self.lr, data_dir=self.data_dir)

    def train(self, query: Query, choices: Choices, labels: Labels) -> None:
        """ train """
        raise web.HTTPNotImplemented

    def rank(self, query: Query, choices: Choices) -> Ranks:
        """
        sort list of indices of topk candidates
        """
        raise web.HTTPNotImplemented
