import os
import json
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from datetime import datetime
from pymongo import MongoClient
from bson import ObjectId  # import for ObjectId serialization

# Load environment variables
load_dotenv()

# MongoDB setup
mongo_uri = os.getenv("MONGO_URI")
db_name = os.getenv("DB_NAME")
collection_name = os.getenv("COLLECTION_NAME")

client = MongoClient(mongo_uri)
db = client[db_name]
collection = db[collection_name]

app = Flask(__name__)

# Helper: validate guest
def is_valid_guest(email):
    if not email:
        return False
    return (
        not email.endswith('@gmail.com') and
        not email.endswith('@circleback.ai') and
        not email.endswith('.calendar.google.com')
    )

# Helper: convert Mongo ObjectId
def serialize_mongo_doc(doc):
    doc["_id"] = str(doc["_id"])
    return doc

# Route
@app.route('/circleback-webhook', methods=['POST'])
def receive_transcript():
    payload = request.json

    # 1. Extract transcript segments
    segments = payload.get("transcript", [])
    transcript_str = json.dumps([
        {
            "speaker": s.get("speaker"),
            "text": s.get("text"),
            "timestamp": s.get("timestamp")
        }
        for s in segments
    ])

    # 2. Extract attendees
    attendees = payload.get("attendees", [])
    team_attendee = next((a for a in attendees if a.get("email", "").endswith("@gmail.com")), None)
    POC = team_attendee.get("name") if team_attendee else ""

    # 3. Extract guest company
    guest = next((a for a in attendees if is_valid_guest(a.get("email"))), None)
    company = guest.get("email").split("@")[1] if guest and "@" in guest.get("email") else "unknown"

    # 4. Build Mongo document
    doc = {
        "organization": "",
        "company": company,
        "transcripts": transcript_str,
        "id": payload.get("id"),
        "POC": POC,
        "received_at": datetime.utcnow()
    }

    # 5. Insert into MongoDB
    result = collection.insert_one(doc)
    doc["_id"] = result.inserted_id

    # 6. Return response (with _id serialized)
    return jsonify({
        "status": "success",
        "message": "Transcript processed",
        "data": serialize_mongo_doc(doc)
    }), 200

# Entry point
if __name__ == '__main__':
    port = int(os.getenv("PORT", 5001))
    app.run(host='0.0.0.0', port=port)
