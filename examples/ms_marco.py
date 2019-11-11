import csv, os
import requests
from elasticsearch import Elasticsearch
from collections import defaultdict
import time

INDEX = 'ms_marco'
# ES_HOST = '35.238.60.182'
# ES_PORT = 9200
ES_HOST = 'localhost'
ES_PORT = 53001
DATA_PATH = '.'
TOPK = 1000
REQUEST_TIMEOUT = 10000

es = Elasticsearch(host=ES_HOST,port=ES_PORT,timeout=REQUEST_TIMEOUT)


def timeit(fn, *args, **kwargs):
    start = time.time()
    res = fn(*args, **kwargs)
    print("took %s seconds to run %s" % (time.time() - start, fn.__name__))
    return res


def eval():
    qrels = set()
    qid_count = defaultdict(int)

    with open(os.path.join(DATA_PATH, 'qrels.dev.small.tsv')) as fh:
        data = csv.reader(fh, delimiter='\t')
        for qid, _, doc_id, _ in data:
            qrels.add((qid, doc_id))

    with open(os.path.join(DATA_PATH, 'queries.dev.tsv')) as fh:
        data = csv.reader(fh, delimiter='\t')
        total = 0
        for qid, query in data:
            total += 1
            res = timeit(es.search, index=INDEX, body={
                "size": TOPK,
                "query": {
                    "match": {
                        "passage": {
                            "query": query
                        }
                    }
                }
            }, filter_path=['hits.hits._*'])

            for rank, hit in enumerate(res['hits']['hits']):
                if (qid, hit['_id']) in qrels:
                    print(qid, ' ', rank)
                    qid_count[qid] = max(qid_count[qid], (1.0 / (float(rank + 1))))
                    mrr = sum(qid_count.values()) / total
                    print("MRR: %s " % mrr)


if __name__ == '__main__':
    eval()