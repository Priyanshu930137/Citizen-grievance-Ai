import os
import json
import uuid
from difflib import SequenceMatcher

import imagehash
from PIL import Image
from dotenv import load_dotenv
from google import genai


# ============================================================
# ENVIRONMENT
# ============================================================

load_dotenv()


# ============================================================
# GEMINI CLIENT
# ============================================================

client = None


def get_gemini_client():
    """
    Creates the Gemini client only when it is actually needed.
    This prevents the application from crashing during startup
    if the Gemini API key is missing.
    """

    global client

    if client is not None:
        return client

    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY is not configured. "
            "Please add GEMINI_API_KEY to the Render environment variables."
        )

    client = genai.Client(api_key=api_key)

    return client


# ============================================================
# TEMPORARY DUPLICATE STORAGE
# ============================================================

complaints_db = []


# ============================================================
# CHECK DUPLICATE GRIEVANCE
# ============================================================

def check_duplicate(text, img=None, location=""):
    """
    Checks whether a similar grievance already exists.

    Text similarity:
        > 85%

    Image similarity:
        Exact average-hash match

    Location must also match.
    """

    new_hash = None

    # Calculate image hash only when an image exists
    if img is not None:
        try:
            new_hash = str(imagehash.average_hash(img))
        except Exception:
            new_hash = None

    for item in complaints_db:

        old_text = item.get("text", "")
        old_location = item.get("location", "")

        # Text similarity
        score = SequenceMatcher(
            None,
            text.lower(),
            old_text.lower()
        ).ratio()

        text_matches = score > 0.85

        # Image similarity
        image_matches = (
            new_hash is not None
            and new_hash == item.get("image_hash")
        )

        # Location comparison
        location_matches = (
            old_location.lower() == location.lower()
        )

        if (
            (text_matches or image_matches)
            and location_matches
        ):
            return item

    return None


# ============================================================
# ANALYZE GRIEVANCE
# ============================================================

def analyze_grievance(
    subject,
    description,
    image_path=None,
    location=""
):
    """
    Analyze a citizen grievance using Gemini AI.

    Parameters:
        subject      -> Complaint title
        description  -> Complaint description
        image_path   -> Optional image path
        location     -> Complaint location

    image_path and location are optional so that the existing
    grievance API continues working without requiring changes
    immediately.
    """

    print("========================================")
    print("🔥 GEMINI AI RUNNING")
    print("========================================")

    print("Subject:", subject)
    print("Location:", location)
    print("Image path:", image_path)

    # ========================================================
    # OPEN IMAGE IF PROVIDED
    # ========================================================

    img = None

    if image_path and os.path.exists(image_path):

        try:
            img = Image.open(image_path)

            print("✅ Image loaded successfully")

        except Exception as e:

            print("⚠️ Could not open image:", str(e))

            img = None

    else:

        print("ℹ️ No image provided")


    # ========================================================
    # GEMINI PROMPT
    # ========================================================

    prompt = f"""
You are Citizen Connect AI, an AI assistant for a
public grievance management system.

Analyze the citizen complaint carefully.

Complaint Title:
{subject}

Complaint Description:
{description}

Location:
{location}

Determine:

1. Category
2. Priority
3. Responsible Department
4. Short AI-generated summary/reason

Priority must be one of:

High
Medium
Low

Return ONLY valid JSON.

Do not use markdown.
Do not use ```json.
Do not add explanations outside JSON.

Required format:

{{
    "category": "",
    "priority": "",
    "department": "",
    "summary": ""
}}
"""


    # ========================================================
    # PREPARE GEMINI CONTENT
    # ========================================================

    if img is not None:

        contents = [
            prompt,
            img
        ]

    else:

        contents = prompt


    # ========================================================
    # CALL GEMINI
    # ========================================================

    try:

        response = get_gemini_client().models.generate_content(
            model="gemini-2.5-flash",
            contents=contents,
            config={
                "response_mime_type": "application/json"
            }
        )

        print("✅ Gemini response received")

    except Exception as e:

        print("❌ Gemini API error:")
        print(str(e))

        # Safe fallback
        result = {
            "category": "General",
            "priority": "Medium",
            "department": "Unassigned",
            "summary": "AI processing could not be completed."
        }

        return create_grievance_result(
            result,
            subject,
            description,
            location,
            img
        )


    # ========================================================
    # GET GEMINI RESPONSE TEXT
    # ========================================================

    clean_text = ""

    try:

        clean_text = response.text.strip()

    except Exception:

        clean_text = ""


    print("Gemini raw response:")
    print(clean_text)


    # ========================================================
    # REMOVE MARKDOWN JSON FENCES IF PRESENT
    # ========================================================

    if clean_text.startswith("```json"):

        clean_text = clean_text[7:]

    elif clean_text.startswith("```"):

        clean_text = clean_text[3:]


    if clean_text.endswith("```"):

        clean_text = clean_text[:-3]


    clean_text = clean_text.strip()


    # ========================================================
    # PARSE JSON
    # ========================================================

    try:

        result = json.loads(clean_text)

        print("✅ Gemini JSON parsed successfully")

    except (json.JSONDecodeError, TypeError):

        print("⚠️ Gemini returned invalid JSON")

        result = {
            "category": "General",
            "priority": "Medium",
            "department": "Unassigned",
            "summary": "AI processing error."
        }


    # ========================================================
    # ENSURE REQUIRED FIELDS EXIST
    # ========================================================

    if not isinstance(result, dict):

        result = {
            "category": "General",
            "priority": "Medium",
            "department": "Unassigned",
            "summary": "AI processing error."
        }


    result["category"] = result.get(
        "category",
        "General"
    ) or "General"


    result["priority"] = result.get(
        "priority",
        "Medium"
    ) or "Medium"


    result["department"] = result.get(
        "department",
        "Unassigned"
    ) or "Unassigned"


    result["summary"] = result.get(
        "summary",
        ""
    ) or ""


    # ========================================================
    # NORMALIZE PRIORITY
    # ========================================================

    priority = str(
        result["priority"]
    ).strip().capitalize()


    if priority not in [
        "High",
        "Medium",
        "Low"
    ]:

        priority = "Medium"


    result["priority"] = priority


    # ========================================================
    # URGENT KEYWORD OVERRIDE
    # ========================================================

    urgent_words = [
        "accident",
        "fire",
        "electric shock",
        "flood",
        "emergency",
        "collapse"
    ]


    full_description = (
        str(subject)
        + " "
        + str(description)
    ).lower()


    if any(
        word in full_description
        for word in urgent_words
    ):

        result["priority"] = "High"

        print(
            "🚨 Priority automatically changed to HIGH"
        )


    # ========================================================
    # RETURN RESULT
    # ========================================================

    return create_grievance_result(
        result,
        subject,
        description,
        location,
        img
    )


# ============================================================
# CREATE FINAL GRIEVANCE RESULT
# ============================================================

def create_grievance_result(
    result,
    subject,
    description,
    location,
    img=None
):
    """
    Creates the final standardized response returned
    by analyze_grievance().
    """

    complaint_id = (
        "CC-"
        + str(uuid.uuid4())[:8].upper()
    )


    # ========================================================
    # IMAGE HASH
    # ========================================================

    image_hash = None

    if img is not None:

        try:

            image_hash = str(
                imagehash.average_hash(img)
            )

        except Exception:

            image_hash = None


    # ========================================================
    # TEMPORARY STORE
    # ========================================================

    complaints_db.append(
        {
            "complaint_id": complaint_id,
            "text": (
                str(subject)
                + " "
                + str(description)
            ),
            "location": location or "",
            "image_hash": image_hash
        }
    )


    # ========================================================
    # FINAL RESPONSE
    # ========================================================

    final_result = {

        "complaint_id": complaint_id,

        "category": result.get(
            "category",
            "General"
        ),

        "priority": result.get(
            "priority",
            "Medium"
        ),

        "department": result.get(
            "department",
            "Unassigned"
        ),

        "reason": result.get(
            "summary",
            ""
        )
    }


    print("========================================")
    print("✅ AI ANALYSIS COMPLETE")
    print("Complaint ID:", complaint_id)
    print("Category:", final_result["category"])
    print("Priority:", final_result["priority"])
    print("Department:", final_result["department"])
    print("========================================")


    return final_result