"""Class to instantiate a mongo class, housing the connection to the mongo engine
and the database.
"""
import pymongo

class MongoInterface():
    def __init__(self):
        self.client = pymongo.MongoClient("mongodb://localhost:27017/")
        self.db = self.client["drip_vision"]
        self.collection_name = "items"
        self.collection = self.db[self.collection_name]

    # Define a function to insert a new document into the collection
    def insert_product(self, document):
        self.collection.insert_one(document)

    # Define a function to find documents in the collection
    def find_products(self, query):
        documents = self.collection.find(query)
        return list(documents)