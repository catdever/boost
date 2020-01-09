"""Base Class for ranking models"""

from typing import List
from nboost.logger import set_logger
from nboost import defaults


class BaseModel:
    """Base Class for Transformer Models"""
    def __init__(self, model_dir: type(defaults.model_dir) = defaults.model_dir,
                 batch_size: type(defaults.batch_size) = defaults.batch_size,
                 max_seq_len: type(defaults.max_seq_len) = defaults.max_seq_len,
                 filter_results: type(defaults.filter_results) = defaults.filter_results,
                 verbose: type(defaults.verbose) = defaults.verbose,
                 lr: type(defaults.lr) = defaults.lr, **_):
        """Model dir will be a full path if the binary is present, and will
        be just the name of the "model_dir" if it is not."""
        super().__init__()
        self.filter_results = filter_results
        self.model_dir = model_dir
        self.lr = lr
        self.max_seq_len = max_seq_len
        self.batch_size = batch_size
        self.logger = set_logger(model_dir, verbose=verbose)

    def rank(self, query: str, choices: List[str]) -> List[int]:
        """assign relative ranks to each choice"""

    def close(self):
        """Close the model"""
