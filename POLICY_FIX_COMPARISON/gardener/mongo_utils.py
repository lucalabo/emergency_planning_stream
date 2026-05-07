import time
import pymongo
from pymongo import MongoClient

class MongoUtils:
    def __init__(self, uri="mongodb://localhost:27017/", db_name="gardener_db"):
        self.client = MongoClient(uri)
        self.db = self.client[db_name]
        self.input_collection = self.db["input_stream"]
        self.output_collection = self.db["output_stream"]

    def write_state(self, timestamp, state_data):
        """
        Writes the current state to the input collection.
        state_data should be a dictionary where keys are atom names 
        and values are lists of dictionaries (arguments).
        """
        document = {"timestamp": timestamp}
        document.update(state_data)
        self.input_collection.insert_one(document)
        # print(f"DEBUG: Written state to MongoDB with timestamp {timestamp}")

    def poll_latest_result(self, last_timestamp=None, timeout=None, interval=0.1):
        """
        Polls the output collection for the most recent document whose timestamp is newer than ``last_timestamp``.
        If ``last_timestamp`` is ``None`` it returns the first document found (the latest one).
        Returns the document if found, otherwise ``None`` after ``timeout`` seconds.
        """
        start_time = time.time()
        while True:
            # Find the latest document sorted by timestamp descending
            latest_doc = self.output_collection.find_one(sort=[("timestamp", -1)])
            if latest_doc:
                doc_ts = latest_doc.get("timestamp")
                if last_timestamp is None or doc_ts > last_timestamp:
                    return latest_doc
            if timeout is not None and time.time() - start_time > timeout:
                return None
            time.sleep(interval)


    def clear_collections(self):
        """
        Clears both input and output collections.
        """
        self.input_collection.delete_many({})
        self.output_collection.delete_many({})
        print("[MongoUtils] Collections cleared.")
