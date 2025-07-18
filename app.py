# app.py
import os
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from datetime import datetime
# db.py
import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

mongo_uri = os.getenv("MONGO_URI")
db_name = os.getenv("DB_NAME")
collection_name = os.getenv("COLLECTION_NAME")

client = MongoClient(mongo_uri)
db = client[db_name]
collection = db[collection_name]

app = Flask(__name__)

@app.route('/circleback-webhook', methods=['POST'])
def receive_transcript():
    data = request.json

    company = data.get('company')
    meeting = data.get('meeting')
    transcript = data.get('transcript')

    if not (company and meeting and transcript):
        return jsonify({"error": "Missing company/meeting/transcript"}), 400

    collection.insert_one({
        "company": company,
        "meeting": meeting,
        "transcript": transcript,
        "received_at": datetime.utcnow()
    })

    return jsonify({"status": "success", "message": "Transcript saved"}), 200

if __name__ == '__main__':
    port = int(os.getenv("PORT", 5001))
    app.run(host='0.0.0.0', port=port)
