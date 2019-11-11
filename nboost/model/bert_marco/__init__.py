from queue import Queue
from threading import Thread
from ...base.types import Ranks

import numpy as np
import tensorflow as tf
import os

from . import modeling, tokenization
from ..base import BaseModel


class BertMarcoModel(BaseModel):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.output_q = Queue()
        self.input_q = Queue()

        self.vocab_file = os.path.join(os.path.dirname(self.model_ckpt), 'vocab.txt')
        self.bert_config_file = os.path.join(os.path.dirname(self.model_ckpt), 'bert_config.json')

        model_thread = Thread(target=self.run_model)
        model_thread.start()

    def model_fn_builder(self, bert_config, num_labels, init_checkpoint):
        """Returns `model_fn` closure for TPUEstimator."""

        def model_fn(features, labels, mode, params):  # pylint: disable=unused-argument
            """The `model_fn` for TPUEstimator."""

            input_ids = features["input_ids"]
            input_mask = features["input_mask"]
            segment_ids = features["segment_ids"]
            label_ids = features["label_ids"]

            (total_loss, per_example_loss, log_probs) = self.create_model(
                bert_config, input_ids, input_mask, segment_ids, label_ids,
                num_labels)

            tvars = tf.trainable_variables()

            (assignment_map, initialized_variable_names
             ) = modeling.get_assignment_map_from_checkpoint(tvars, init_checkpoint)

            tf.train.init_from_checkpoint(init_checkpoint, assignment_map)

            output_spec = tf.estimator.EstimatorSpec(
                mode=mode,
                predictions={
                    "log_probs": log_probs,
                    "label_ids": label_ids,
                })
            return output_spec

        return model_fn

    def input_fn(self):
        """The actual input function."""

        output_types = {
            "input_ids": tf.int32,
            "segment_ids": tf.int32,
            "input_mask": tf.int32,
            "label_ids": tf.int32,
        }
        dataset = tf.data.Dataset.from_generator(self.feature_generator, output_types)

        dataset = dataset.padded_batch(
            batch_size=self.batch_size,
            padded_shapes={
                "input_ids": [self.max_seq_len],
                "segment_ids": [self.max_seq_len],
                "input_mask": [self.max_seq_len],
                "label_ids": [],
            },
            padding_values={
                "input_ids": 0,
                "segment_ids": 0,
                "input_mask": 0,
                "label_ids": 0,
            },
            drop_remainder=True)

        return dataset

    def run_model(self, model: BaseModel):
        bert_config = modeling.BertConfig.from_json_file(self.bert_config_file)
        assert self.max_seq_len <= bert_config.max_position_embeddings

        run_config = tf.estimator.RunConfig(model_dir=self.data_dir)

        model_fn = self.model_fn_builder(
            bert_config=bert_config,
            num_labels=2,
            init_checkpoint=model.model_ckpt)

        estimator = tf.estimator.Estimator(
            model_fn=model_fn,
            config=run_config)

        result = estimator.predict(input_fn=self.input_fn,
                                   yield_single_examples=True)

        for item in result:
            self.output_q.put((item["log_probs"], item["label_ids"]))

    def create_model(self, bert_config, input_ids, input_mask, segment_ids,
                     labels, num_labels):
        """Creates a classification model."""
        model = modeling.BertModel(
            config=bert_config,
            is_training=False,
            input_ids=input_ids,
            input_mask=input_mask,
            token_type_ids=segment_ids,
            use_one_hot_embeddings=False)

        output_layer = model.get_pooled_output()
        hidden_size = output_layer.shape[-1].value

        output_weights = tf.get_variable(
            "output_weights", [num_labels, hidden_size],
            initializer=tf.truncated_normal_initializer(stddev=0.02))

        output_bias = tf.get_variable(
            "output_bias", [num_labels], initializer=tf.zeros_initializer())

        with tf.variable_scope("loss"):
            logits = tf.matmul(output_layer, output_weights, transpose_b=True)
            logits = tf.nn.bias_add(logits, output_bias)
            log_probs = tf.nn.log_softmax(logits, axis=-1)

            one_hot_labels = tf.one_hot(labels, depth=num_labels, dtype=tf.float32)

            per_example_loss = -tf.reduce_sum(one_hot_labels * log_probs, axis=-1)
            loss = tf.reduce_mean(per_example_loss)

            return (loss, per_example_loss, log_probs)

    def feature_generator(self):
        tokenizer = tokenization.FullTokenizer(vocab_file=self.vocab_file, do_lower_case=True)
        while True:
            query, candidates = self.input_q.get()
            query = tokenization.convert_to_unicode(query)
            query_token_ids = tokenization.convert_to_bert_input(
                text=query, max_seq_length=self.max_seq_len, tokenizer=tokenizer,
                add_cls=True)

            for i, doc_text in enumerate(candidates):
                doc_token_id = tokenization.convert_to_bert_input(
                    text=tokenization.convert_to_unicode(doc_text),
                    max_seq_length=self.max_seq_len - len(query_token_ids),
                    tokenizer=tokenizer,
                    add_cls=False)

                query_ids = query_token_ids
                doc_ids = doc_token_id
                input_ids = query_ids + doc_ids

                query_segment_id = [0] * len(query_ids)
                doc_segment_id = [1] * len(doc_ids)
                segment_ids = query_segment_id + doc_segment_id

                input_mask = [1] * len(input_ids)

                features = {
                    "input_ids": input_ids,
                    "segment_ids": segment_ids,
                    "input_mask": input_mask,
                    "label_ids": 0
                }
                yield features

    def rank(self, query, choices):
        candidates = [c.decode() for c in choices]
        self.input_q.put((query.decode(), candidates))

        results = [self.output_q.get() for _ in range(len(candidates))]
        log_probs, labels = zip(*results)
        log_probs = np.stack(log_probs).reshape(-1, 2)
        scores = log_probs[:, 1]
        pred_docs = scores.argsort()[::-1]
        return Ranks(pred_docs)
