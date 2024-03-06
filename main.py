from bs4 import BeautifulSoup
import requests
from pymongo import MongoClient
import json

if __name__ == "__main__":
    client = MongoClient('mongodb://MongoAdmin:mongo123@192.168.96.96:27017/')
    db = client['hh_gb']
    collection = db['hh']
    # фильтрация по возрасту
    old_person = list(collection.find({'age': {'$gte': 50}}))
    print(json.dumps(old_person, indent=4, ensure_ascii=False, default=str))