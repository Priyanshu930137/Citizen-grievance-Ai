import os
import json
import uuid
from difflib import SequenceMatcher
import ImageHash  # Capitalized as imported
from PIL import Image
from dotenv import load_dotenv
from google import genai

load_dotenv()

# Do not create the Gemini client while the application is importing. This
# lets the dashboard and account-management APIs run even when AI analysis has
# not been configured yet.
client = None
complaints_db = []

def get_gemini_client():
    global client
    if client is not None:
        return client
    
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY is not configured. Add it to backend/.env "
            "before submitting AI-analyzed grievances."
        )
    
    client = genai.Client(api_key=api_key)
    return client

def check_duplicate(text, img, location):
    # Calculate image hash only if an image is actually provided
    new_hash = str(ImageHash.average_hash(img)) if img else None
    
    for item in complaints_db:
        score = SequenceMatcher(None, text.lower(), item["text"].lower()).ratio()
        
        # Match if text is similar OR if images match (only if both have images)
        image_matches = (new_hash is not None) and (new_hash == item.get("image_hash"))
        text_matches = score > 0.85
        
        if (text_matches or image_matches) and item["location"].lower() == location.lower():
            return item
            
    return None

def analyze_grievance(subject, description, image_path, location):
    print("🔥 GEMINI AI RUNNING")
    print("image path ", image_path)
    
    # Safely open image if path exists and is not empty
    img = Image.open(image_path) if (image_path and os.path.exists(image_path)) else None
    
    prompt = f"""
    You are Citizen Connect AI. Analyze BOTH the uploaded image and complaint.
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
    
    contents = [prompt, img] if img else prompt
    
    response = get_gemini_client().models.generate_content(
        model="gemini-2.5-flash",  # Updated to standard stable model syntax
        contents=contents,
        config={"response_mime_type": "application/json"}
    )
    
    result = json.loads(response.text)
    
    # Keyword override for priority
    urgent_words = ["accident", "fire", "electric shock", "flood", "emergency", "collapse"]
    if any(word in description.lower() for word in urgent_words):
        result["priority"] = "High"
        
    complaint_id = "CC-" + str(uuid.uuid4())[:8].upper()
    
    return {
        "complaint_id": complaint_id,
        "category": result.get("category", "General"),
        "priority": result.get("priority", "Medium"),
        "department": result.get("department", "Unassigned"),
        "reason": result.get("summary", "")
    }

