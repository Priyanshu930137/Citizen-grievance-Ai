from fastapi import FastAPI, UploadFile, File, Form
from google import genai
from PIL import Image
from dotenv import load_dotenv
import os
import io

# Load .env
load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise RuntimeError("GEMINI_API_KEY is not configured")

client = genai.Client(api_key=api_key)

app = FastAPI(title="Citizen Grievance AI API")


class GrievanceAnalysis(BaseModel):
    category: str
    priority: str
    department: str
    location: str
    summary: str


@app.get("/health")
async def health_check():
    return {"status": "ok"}


@app.post("/analyze", response_model=GrievanceAnalysis)
async def analyze_complaint(
    image: UploadFile = File(...),
    complaint: str = Form(...),
    location: str = Form(...)
):
    if not image.content_type or not image.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="The uploaded file must be an image")

    try:
        img = Image.open(io.BytesIO(await image.read()))
        img.load()
    except (OSError, ValueError) as exc:
        raise HTTPException(status_code=400, detail="The uploaded file is not a valid image") from exc

    prompt = f"""
You are an AI Public Grievance Assistant.

Complaint: {complaint}
Location: {location}

Analyze the image and complaint.

Return ONLY valid JSON matching this schema:
{{
  "category":"",
  "priority":"",
  "department":"",
  "location":"{location}",
  "summary":""
}}
"""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[prompt, img],
        config={"response_mime_type": "application/json"},
    )

    try:
        result = json.loads(response.text)
        return GrievanceAnalysis.model_validate(result)
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        raise HTTPException(status_code=502, detail="The AI returned an invalid analysis") from exc
      