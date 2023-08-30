from pymongo import MongoClient
print("Connecting to database...")
client = MongoClient(
    "mongodb+srv://techzbots:4tQYI1SD64nr8jz5@rankingsbot.h5std55.mongodb.net/?retryWrites=true&w=majority"
)

db = client["techzcloud"]
filesdb = db["files"]
print("Connected to database...")

def save_file_in_db(filename, hash, msg_id=None):
    filesdb.update_one(
        {
            "hash": hash,
        },
        {"$set": {"filename": filename, "msg_id": msg_id}},
        upsert=True,
    )


def is_hash_in_db(hash):
    return data if (data := filesdb.find_one({"hash": hash})) else None
