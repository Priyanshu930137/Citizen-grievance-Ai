from google import genai
from PIL import Image
from dotenv import load_dotenv
from difflib import SequenceMatcher
import imagehash
import os
import json
import uuid


load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
complaints_db = []


def check_duplicate(text, img, location):
    new_hash = str(imagehash.average_hash(img))

    for item in complaints_db:
        score = SequenceMatcher(None, text.lower(), item["text"].lower()).ratio()

        if (score > 0.85 or new_hash == item["image_hash"]) and item["location"].lower() == location.lower():
            return item

    return None


def analyze_grievance(subject, description, image_path, location):
    print("🔥 GEMINI AI RUNNING")
    print("image path ",image_path)

    img = Image.open(image_path)

    duplicate = check_duplicate(description, img, location)
    if duplicate:
        return {
            "complaint_id": duplicate["complaint_id"],
            "category": duplicate["category"],
            "priority": duplicate["priority"],
            "department": duplicate["department"],
            "reason": "This complaint is already registered."
        }

    prompt = f"""
You are Citizen Connect AI.

Analyze BOTH the uploaded image and complaint.

Complaint Title: {subject}
Complaint: {description}
Location: {location}

Return ONLY JSON:
{{
"category":"",
"priority":"High/Medium/Low",
"department":"",
"summary":""
}}
"""

    response = client.models.generate_content(
        model="gemini-3.5-flash-lite",
        contents=[prompt, img],
        config={"response_mime_type": "application/json"}
    )

    result = json.loads(response.text)

    urgent_words = ["accident","fire","electric shock","flood","emergency","collapse"]
    if any(word in description.lower() for word in urgent_words):
        result["priority"] = "High"

    complaint_id = "CC-" + str(uuid.uuid4())[:8].upper()

    complaints_db.append({
        "complaint_id": complaint_id,
        "text": description,
        "image_hash": str(imagehash.average_hash(img)),
        "category": result["category"],
        "priority": result["priority"],
        "department": result["department"],
        "location": location,
        "summary": result["summary"],
        "status": "Pending"
    })

    return {
        "complaint_id": complaint_id,
        "category": result["category"],
        "priority": result["priority"],
        "department": result["department"],
        "reason": result["summary"]
    }