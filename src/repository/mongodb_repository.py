from pymongo import MongoClient
from bson import ObjectId
import gridfs
import datetime
import uuid
import os

# Initialize Mongo client and GridFS
mongo_client = MongoClient(os.environ.get("MY_MONGO_URI"))
db = mongo_client['candidate_resumes_db']
fs = gridfs.GridFS(db)


def save_resume_to_mongo(resume_file):
    upload_timestamp = datetime.datetime.utcnow()

    metadata = {
        'upload_timestamp': upload_timestamp
    }

    resume_id = fs.put(resume_file.read(), filename=str(uuid.uuid4()), metadata=metadata)

    return str(resume_id)


def get_resume_by_id(resume_id):
    return fs.get(ObjectId(resume_id))
