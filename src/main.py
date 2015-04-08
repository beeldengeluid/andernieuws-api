#!/usr/bin/python
from elasticsearch import Elasticsearch
import sys

sys.path.insert(0, 'YOUR_LOCAL_PATH/andernieuws-api/src')

from ASRIndexer import *

class Main(object):

    def __init__(self):
        indexName = 'andernieuws'
        es = Elasticsearch()
        print es.info()
        x = Indexer()
        """ uncomment the following to create an empty index on your local Elasticsearch"""
        #indexer.createIndex(es, indexName, '../resources/settings.json', '../resources/mapping.json')
        """ uncomment the following to index a directory with ASR files"""
        #x.indexASRDirectory('PATH TO YOUR DIRECTORY HOLDING ASR XML FILES', es, indexName)

m = Main()