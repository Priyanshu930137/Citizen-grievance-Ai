# ==========================================
# CITIZEN CONNECT - MAIN BACKEND API
# ==========================================

from pathlib import Path
from collections import Counter
from difflib import SequenceMatcher
import json

from fastapi import (
    FastAPI,
    Depends,
    HTTPException,
    UploadFile,
    File,
    Form
)

from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from sqlalchemy.orm import Session
from sqlalchemy import inspect, text

from PIL import Image
import imagehash

from config import CORS_ORIGINS, AUTHORITY_CREDENTIALS_FILE

from database import (
    engine,
    Base,
    get_db
)

import models
import schemas

from Ai import analyze_grievance
import Ai

print("AI FILE LOADED FROM:", Ai.__file__)
print("AI FUNCTION:", analyze_grievance)


# ==========================================
# CREATE DATABASE TABLES
# ==========================================

# ==========================================
# CREATE FASTAPI APPLICATION
# ==========================================

app = FastAPI(

    title="Citizen Connect API",

    description=(
        "AI Powered Citizen Engagement and "
        "Public Grievance Management System"
    ),

    version="1.0.0"

)
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# ==========================================
# FRONTEND PATH
# ==========================================

BASE_DIR = Path(__file__).resolve().parent.parent

FRONTEND_DIR = BASE_DIR / "frontend"


# ==========================================
# AVAILABLE DEPARTMENTS
# ==========================================

ALLOWED_DEPARTMENTS = [

    "Public Works Department",

    "Water Supply Department",

    "Electricity Department",

    "Municipal Corporation",

    "Police Department",

    "Health Department",

    "Traffic Management Department",

    "Public Administration"

]


# ==========================================
# ALLOWED ROLES
# ==========================================

ALLOWED_ROLES = [

    "citizen",

    "authority",

    "management",

    "technician"

]


# ==========================================
# AUTHORITY BOOTSTRAP
# ==========================================

def load_authority_credentials():
    """Read the single authority account from a simple key=value text file."""
    if not AUTHORITY_CREDENTIALS_FILE.exists():
        raise RuntimeError(
            "Authority credentials file is missing: "
            f"{AUTHORITY_CREDENTIALS_FILE}"
        )

    credentials = {}
    for line in AUTHORITY_CREDENTIALS_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            raise RuntimeError("Invalid authority credentials file format.")
        key, value = line.split("=", 1)
        credentials[key.strip()] = value.strip()

    required_keys = {"name", "email", "password"}
    if not required_keys.issubset(credentials):
        raise RuntimeError(
            "Authority credentials file must contain name, email, and password."
        )
    return credentials


def ensure_authority_account():
    """Create or refresh the only authority account from the credentials file."""
    credentials = load_authority_credentials()
    db = next(get_db())
    try:
        authority = db.query(models.User).filter(
            models.User.email == credentials["email"]
        ).first()

        if authority:
            authority.name = credentials["name"]
            authority.password = credentials["password"]
            authority.role = "authority"
            authority.department = None
        else:
            db.add(models.User(
                name=credentials["name"],
                email=credentials["email"],
                password=credentials["password"],
                role="authority"
            ))
        db.commit()
    finally:
        db.close()


def is_configured_authority(user):
    """Only the account in the credentials file has authority privileges."""
    credentials = load_authority_credentials()
    return user.role == "authority" and user.email == credentials["email"]


def ensure_grievance_columns():
    """Add duplicate/evidence fields to existing SQLite databases safely."""
    existing_columns = {
        column["name"] for column in inspect(engine).get_columns("grievances")
    }
    columns = {
        "image_hash": "VARCHAR(64)",
        "image_metadata": "TEXT",
        "parent_grievance_id": "INTEGER",
        "is_duplicate": "INTEGER NOT NULL DEFAULT 0",
        "duplicate_confidence": "INTEGER",
        "report_count": "INTEGER NOT NULL DEFAULT 1",
        "verification_status": "VARCHAR(50) NOT NULL DEFAULT 'Pending Review'",
        "verification_notes": "TEXT"
    }
    with engine.begin() as connection:
        for name, definition in columns.items():
            if name not in existing_columns:
                connection.execute(text(
                    f"ALTER TABLE grievances ADD COLUMN {name} {definition}"
                ))


def normalize_text(value):
    return " ".join((value or "").lower().split())


def get_image_evidence(image_path):
    """Return a perceptual hash and non-conclusive metadata review notes."""
    if not image_path:
        return None, None, []

    try:
        with Image.open(image_path) as image_file:
            image_hash = str(imagehash.phash(image_file))
            exif = image_file.getexif()
            metadata = {
                str(key): str(value)
                for key, value in exif.items()
                if str(value).strip()
            }
    except Exception:
        return None, None, ["The uploaded file could not be verified as a readable image."]

    flags = []
    if not metadata:
        flags.append("No camera metadata was present; this alone does not prove the image is false.")
    return image_hash, json.dumps(metadata), flags


def find_probable_duplicate(db, subject, description, location, image_hash):
    """Find an open primary grievance with matching area and evidence."""
    candidates = db.query(models.Grievance).filter(
        models.Grievance.parent_grievance_id.is_(None),
        ~models.Grievance.status.in_(["Resolved", "Rejected"])
    ).all()

    new_text = normalize_text(subject + " " + description)
    new_location = normalize_text(location)
    best_match = None
    best_score = 0
    for candidate in candidates:
        location_score = SequenceMatcher(
            None, new_location, normalize_text(candidate.location)
        ).ratio()
        text_score = SequenceMatcher(
            None, new_text, normalize_text(candidate.subject + " " + candidate.description)
        ).ratio()
        same_image = bool(image_hash and candidate.image_hash == image_hash)
        score = 100 if same_image and location_score >= 0.60 else round(
            (location_score * 40 + text_score * 60) * 100
        )
        if location_score >= 0.70 and (same_image or score >= 75) and score > best_score:
            best_match = candidate
            best_score = score
    return best_match, best_score


Base.metadata.create_all(bind=engine)
ensure_grievance_columns()
ensure_authority_account()


# ==========================================
# API HOME
# ==========================================

@app.get("/api")
def api_home():

    return {

        "message":
            "Citizen Connect API is running successfully"

    }


# ==========================================
# USER REGISTRATION
# ==========================================

@app.post("/api/register")
def register_user(

    user: schemas.UserRegister,

    db: Session = Depends(get_db)

):

    # ======================================
    # CHECK EXISTING USER
    # ======================================

    existing_user = db.query(
        models.User
    ).filter(

        models.User.email == user.email

    ).first()


    if existing_user:

        raise HTTPException(

            status_code=400,

            detail="Email is already registered."

        )


    # Public registration is exclusively for citizens.  Never trust a role
    # sent by a registration form, even when a client exposes such a field.
    if user.role != "citizen" or user.department is not None:
        raise HTTPException(
            status_code=403,
            detail="Public registration is available only for citizen accounts."
        )


    # ======================================
    # CREATE USER
    # ======================================

    new_user = models.User(

        name=user.name,

        email=user.email,

        password=user.password,

        role="citizen",

        department=None

    )


    db.add(new_user)

    db.commit()

    db.refresh(new_user)


    return {

        "message":
            "Registration successful",

        "user": {

            "id": new_user.id,

            "name": new_user.name,

            "email": new_user.email,

            "role": new_user.role,

            "department": new_user.department

        }

    }


# ==========================================
# STAFF ACCOUNT PROVISIONING
# ==========================================

@app.post("/api/staff-accounts")
def create_staff_account(
    account: schemas.StaffAccountCreate,
    db: Session = Depends(get_db)
):
    """Allow authority -> management and management -> own-department technician."""
    account_name = account.name.strip()
    account_email = str(account.email).lower()
    creator_email = str(account.creator_email).lower()

    creator = db.query(models.User).filter(
        models.User.email == creator_email
    ).first()

    if not creator or creator.password != account.creator_password:
        raise HTTPException(status_code=401, detail="Invalid creator credentials.")

    if db.query(models.User).filter(models.User.email == account_email).first():
        raise HTTPException(status_code=400, detail="Email is already registered.")

    if account.role not in {"management", "technician"}:
        raise HTTPException(
            status_code=403,
            detail="Only management and technician accounts can be provisioned."
        )

    if creator.role == "authority":
        if not is_configured_authority(creator):
            raise HTTPException(
                status_code=403,
                detail="Only the configured authority account can create management accounts."
            )
        if account.role != "management":
            raise HTTPException(
                status_code=403,
                detail="Authority can create management accounts only."
            )
        department = account.department
    elif creator.role == "management":
        if account.role != "technician":
            raise HTTPException(
                status_code=403,
                detail="Management can create technician accounts only."
            )
        if account.department and account.department != creator.department:
            raise HTTPException(
                status_code=403,
                detail="Management can create technicians only in its own department."
            )
        department = creator.department
    else:
        raise HTTPException(
            status_code=403,
            detail="Only authority and management accounts can create staff accounts."
        )

    if department not in ALLOWED_DEPARTMENTS:
        raise HTTPException(status_code=400, detail="A valid department is required.")

    new_user = models.User(
        name=account_name,
        email=account_email,
        password=account.password,
        role=account.role,
        department=department
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {
        "message": "Staff account created successfully.",
        "user": {
            "id": new_user.id,
            "name": new_user.name,
            "email": new_user.email,
            "role": new_user.role,
            "department": new_user.department
        }
    }


@app.get("/api/staff-accounts/management")
def get_management_accounts(db: Session = Depends(get_db)):
    """Return management accounts for the authority dashboard."""
    management_accounts = db.query(models.User).filter(
        models.User.role == "management"
    ).order_by(models.User.department, models.User.name).all()

    return {
        "count": len(management_accounts),
        "accounts": [
            {
                "id": account.id,
                "name": account.name,
                "email": account.email,
                "department": account.department,
                "created_at": account.created_at
            }
            for account in management_accounts
        ]
    }


# ==========================================
# USER LOGIN
# ==========================================

@app.post("/api/login")
def login_user(

    user: schemas.UserLogin,

    db: Session = Depends(get_db)

):

    # ======================================
    # FIND USER
    # ======================================

    existing_user = db.query(
        models.User
    ).filter(

        models.User.email == user.email

    ).first()


    if not existing_user:

        raise HTTPException(

            status_code=401,

            detail="Invalid email or password."

        )


    # ======================================
    # PASSWORD CHECK
    # ======================================

    if existing_user.password != user.password:

        raise HTTPException(

            status_code=401,

            detail="Invalid email or password."

        )


    # ======================================
    # ROLE CHECK
    # ======================================

    if existing_user.role != user.role:

        raise HTTPException(

            status_code=403,

            detail=(
                "This account does not have "
                "the selected role."
            )

        )


    return {

        "message":
            "Login successful",

        "user": {

            "id": existing_user.id,

            "name": existing_user.name,

            "email": existing_user.email,

            "role": existing_user.role,

            "department": existing_user.department

        }

    }


# ==========================================
# CREATE GRIEVANCE
# CITIZEN USE
# ==========================================

@app.post("/api/grievances")
async def create_grievance(
    citizen_id: int = Form(...),
    citizen_name: str = Form(...),
    citizen_email: str = Form(...),
    citizen_phone: str = Form(...),
    subject: str = Form(...),
    description: str = Form(...),
    location: str = Form(...),
    image: UploadFile = File(None),
    db: Session = Depends(get_db)
):
    image_path = None

    if image:
        image_path = UPLOAD_DIR / image.filename
        with open(image_path, "wb") as buffer:
            buffer.write(await image.read())


    # ======================================
    # VALIDATE CITIZEN
    # ======================================

    citizen = db.query(
        models.User
    ).filter(

        models.User.id == citizen_id,

        models.User.role == "citizen"

    ).first()


    if not citizen:

        raise HTTPException(

            status_code=404,

            detail="Citizen account not found."

        )
    # ======================================
    # EVIDENCE AND DUPLICATE CHECK
    # ======================================

    image_hash, image_metadata, verification_flags = get_image_evidence(image_path)
    primary_grievance, confidence = find_probable_duplicate(
        db, subject, description, location, image_hash
    )

    if primary_grievance:
        duplicate_report = models.Grievance(
            citizen_id=citizen_id,
            citizen_name=citizen_name,
            email=citizen_email,
            phone=citizen_phone,
            subject=subject,
            description=description,
            image_url=str(image_path) if image_path else None,
            image_hash=image_hash,
            image_metadata=image_metadata,
            location=location,
            category=primary_grievance.category,
            department=primary_grievance.department,
            priority=primary_grievance.priority,
            ai_reason="Linked to a similar open grievance.",
            status=primary_grievance.status,
            parent_grievance_id=primary_grievance.id,
            is_duplicate=1,
            duplicate_confidence=confidence,
            report_count=1,
            verification_status="Pending Review",
            verification_notes=" ".join(verification_flags) or None
        )
        primary_grievance.report_count = (primary_grievance.report_count or 1) + 1
        db.add(duplicate_report)
        db.commit()
        db.refresh(duplicate_report)

        return {
            "message": "Your report was linked to an existing issue.",
            "grievance_id": duplicate_report.id,
            "is_duplicate": True,
            "duplicate_confidence": confidence,
            "original_grievance_id": primary_grievance.id,
            "original_status": primary_grievance.status,
            "report_count": primary_grievance.report_count
        }

    # ======================================
    # AI ANALYSIS
    # ======================================

    try:
        assessment = analyze_grievance(
            subject,
            description,
            image_path,
            location
        )
        print("Gemini Response:", assessment)

    except Exception as e:
        print("GEMINI ERROR:", e)
        raise HTTPException(
            status_code=500,
            detail=f"Gemini AI Error: {str(e)}"
        )
  
    # ======================================
    # CREATE GRIEVANCE
    # ======================================
    new_grievance = models.Grievance(

    citizen_id=citizen_id,

    citizen_name=citizen_name,

    email=citizen_email,

    phone=citizen_phone,

    subject=subject,

    description=description,

    image_url=str(image_path) if image_path else None,

    image_hash=image_hash,

    image_metadata=image_metadata,

    location=location,

    category=assessment["category"],

    department=assessment["department"],

    priority=assessment["priority"],

    ai_reason=assessment["reason"],

    status="Pending",

    parent_grievance_id=None,

    is_duplicate=0,

    report_count=1,

    verification_status="Pending Review",

    verification_notes=" ".join(verification_flags) or None

)


    # ======================================
    # SAVE
    # ======================================

    db.add(new_grievance)

    db.commit()

    db.refresh(new_grievance)


    return {

        "message":
            "Grievance submitted successfully.",

        "grievance_id":
            new_grievance.id,

        "status":
            new_grievance.status,

        "assessment": {

            "category":
                new_grievance.category,

            "department":
                new_grievance.department,

            "priority":
                new_grievance.priority,

            "reason":
                new_grievance.ai_reason

        }

    }


# ==========================================
# GET ALL GRIEVANCES
# HIGHER AUTHORITY
# ==========================================

@app.get("/api/grievances")
def get_all_grievances(

    db: Session = Depends(get_db)

):

    grievances = db.query(
        models.Grievance
    ).order_by(

        models.Grievance.created_at.desc()

    ).all()


    return grievances


# ==========================================
# GET SINGLE GRIEVANCE
# ==========================================

@app.get("/api/grievances/{grievance_id}")
def get_grievance(

    grievance_id: int,

    db: Session = Depends(get_db)

):

    grievance = db.query(
        models.Grievance
    ).filter(

        models.Grievance.id == grievance_id

    ).first()


    if not grievance:

        raise HTTPException(

            status_code=404,

            detail="Grievance not found."

        )


    return grievance


# ==========================================
# GET CITIZEN GRIEVANCES
# ==========================================

@app.get(
    "/api/citizens/{citizen_id}/grievances"
)
def get_citizen_grievances(

    citizen_id: int,

    db: Session = Depends(get_db)

):

    grievances = db.query(
        models.Grievance
    ).filter(

        models.Grievance.citizen_id == citizen_id

    ).order_by(

        models.Grievance.created_at.desc()

    ).all()


    return grievances


# ==========================================
# GET DEPARTMENT GRIEVANCES
# MANAGEMENT USE
# ==========================================

@app.get(
    "/api/departments/{department_name}/grievances"
)
def get_department_grievances(

    department_name: str,

    db: Session = Depends(get_db)

):

    if department_name not in ALLOWED_DEPARTMENTS:

        raise HTTPException(

            status_code=400,

            detail="Invalid department."

        )


    grievances = db.query(
        models.Grievance
    ).filter(

        models.Grievance.department ==
        department_name

    ).order_by(

        models.Grievance.created_at.desc()

    ).all()


    return grievances


# ==========================================
# GET TECHNICIANS BY DEPARTMENT
# ==========================================

@app.get(
    "/api/departments/{department_name}/technicians"
)
def get_department_technicians(

    department_name: str,

    db: Session = Depends(get_db)

):

    if department_name not in ALLOWED_DEPARTMENTS:

        raise HTTPException(

            status_code=400,

            detail="Invalid department."

        )


    technicians = db.query(
        models.User
    ).filter(

        models.User.role == "technician",

        models.User.department ==
        department_name

    ).all()


    return [

        {

            "id": technician.id,

            "name": technician.name,

            "email": technician.email,

            "department": technician.department

        }

        for technician in technicians

    ]


# ==========================================
# ASSIGN GRIEVANCE TO TECHNICIAN
# DEPARTMENT MANAGEMENT
# ==========================================

@app.put(
    "/api/grievances/{grievance_id}/assign"
)
def assign_grievance(

    grievance_id: int,

    assignment: schemas.GrievanceAssign,

    db: Session = Depends(get_db)

):

    # ======================================
    # FIND GRIEVANCE
    # ======================================

    grievance = db.query(
        models.Grievance
    ).filter(

        models.Grievance.id == grievance_id

    ).first()


    if not grievance:

        raise HTTPException(

            status_code=404,

            detail="Grievance not found."

        )


    # ======================================
    # FIND TECHNICIAN
    # ======================================

    technician = db.query(
        models.User
    ).filter(

        models.User.id ==
        assignment.technician_id,

        models.User.role == "technician"

    ).first()


    if not technician:

        raise HTTPException(

            status_code=404,

            detail="Technician not found."

        )


    # ======================================
    # DEPARTMENT CHECK
    # ======================================

    if technician.department != grievance.department:

        raise HTTPException(

            status_code=400,

            detail=(
                "Technician does not belong "
                "to the grievance department."
            )

        )


    # ======================================
    # ASSIGN
    # ======================================

    grievance.assigned_technician_id = (
        technician.id
    )

    grievance.assigned_technician_name = (
        technician.name
    )

    grievance.status = "Assigned"


    db.commit()

    db.refresh(grievance)


    return {

        "message":
            "Grievance assigned successfully.",

        "grievance_id":
            grievance.id,

        "technician_id":
            technician.id,

        "technician":
            technician.name,

        "status":
            grievance.status

    }


# ==========================================
# GET TECHNICIAN GRIEVANCES
# ==========================================

@app.get(
    "/api/technicians/{technician_id}/grievances"
)
def get_technician_grievances(

    technician_id: int,

    db: Session = Depends(get_db)

):

    grievances = db.query(
        models.Grievance
    ).filter(

        models.Grievance.assigned_technician_id ==
        technician_id

    ).order_by(

        models.Grievance.created_at.desc()

    ).all()


    return grievances


# ==========================================
# TECHNICIAN UPDATE GRIEVANCE
# ==========================================

@app.put(
    "/api/grievances/{grievance_id}/technician-update"
)
def technician_update_grievance(

    grievance_id: int,

    update: schemas.TechnicianUpdate,

    db: Session = Depends(get_db)

):

    grievance = db.query(
        models.Grievance
    ).filter(

        models.Grievance.id == grievance_id

    ).first()


    if not grievance:

        raise HTTPException(

            status_code=404,

            detail="Grievance not found."

        )


    # ======================================
    # VALIDATE STATUS
    # ======================================

    allowed_statuses = [

        "In Progress",

        "Resolved"

    ]


    if update.status not in allowed_statuses:

        raise HTTPException(

            status_code=400,

            detail="Invalid technician status."

        )


    # ======================================
    # UPDATE GRIEVANCE
    # ======================================

    grievance.diagnosis = update.diagnosis

    grievance.resolution_note = (
        update.resolution_note
    )

    grievance.status = update.status


    db.commit()

    db.refresh(grievance)


    return {

        "message":
            "Grievance updated successfully.",

        "grievance_id":
            grievance.id,

        "status":
            grievance.status

    }


# ==========================================
# UPDATE GRIEVANCE STATUS
# HIGHER AUTHORITY
# ==========================================

@app.put(
    "/api/grievances/{grievance_id}/status"
)
def update_grievance_status(

    grievance_id: int,

    update: schemas.GrievanceStatusUpdate,

    db: Session = Depends(get_db)

):

    grievance = db.query(
        models.Grievance
    ).filter(

        models.Grievance.id == grievance_id

    ).first()


    if not grievance:

        raise HTTPException(

            status_code=404,

            detail="Grievance not found."

        )


    allowed_statuses = [

        "Pending",

        "Assigned",

        "In Progress",

        "Resolved",

        "Rejected"

    ]


    if update.status not in allowed_statuses:

        raise HTTPException(

            status_code=400,

            detail="Invalid status."

        )


    grievance.status = update.status


    db.commit()

    db.refresh(grievance)


    return {

        "message":
            "Status updated successfully.",

        "grievance_id":
            grievance.id,

        "status":
            grievance.status

    }


# ==========================================
# UPDATE GRIEVANCE DEPARTMENT
# HIGHER AUTHORITY
# ==========================================

@app.put(
    "/api/grievances/{grievance_id}/department"
)
def update_grievance_department(

    grievance_id: int,

    update: schemas.GrievanceDepartmentUpdate,

    db: Session = Depends(get_db)

):

    if update.department not in ALLOWED_DEPARTMENTS:

        raise HTTPException(

            status_code=400,

            detail="Invalid department."

        )


    grievance = db.query(
        models.Grievance
    ).filter(

        models.Grievance.id == grievance_id

    ).first()


    if not grievance:

        raise HTTPException(

            status_code=404,

            detail="Grievance not found."

        )


    grievance.department = update.department


    db.commit()

    db.refresh(grievance)


    return {

        "message":
            "Department updated successfully.",

        "department":
            grievance.department

    }


# ==========================================
# UPDATE GRIEVANCE PRIORITY
# HIGHER AUTHORITY
# ==========================================

@app.put(
    "/api/grievances/{grievance_id}/priority"
)
def update_grievance_priority(

    grievance_id: int,

    update: schemas.GrievancePriorityUpdate,

    db: Session = Depends(get_db)

):

    allowed_priorities = [

        "Low",

        "Medium",

        "High"

    ]


    if update.priority not in allowed_priorities:

        raise HTTPException(

            status_code=400,

            detail="Invalid priority."

        )


    grievance = db.query(
        models.Grievance
    ).filter(

        models.Grievance.id == grievance_id

    ).first()


    if not grievance:

        raise HTTPException(

            status_code=404,

            detail="Grievance not found."

        )


    grievance.priority = update.priority


    db.commit()

    db.refresh(grievance)


    return {

        "message":
            "Priority updated successfully.",

        "priority":
            grievance.priority

    }


# ==========================================
# VERIFY GRIEVANCE EVIDENCE
# HIGHER AUTHORITY
# ==========================================

@app.put("/api/grievances/{grievance_id}/verification")
def update_grievance_verification(
    grievance_id: int,
    update: schemas.GrievanceVerificationUpdate,
    db: Session = Depends(get_db)
):
    grievance = db.query(models.Grievance).filter(
        models.Grievance.id == grievance_id
    ).first()
    if not grievance:
        raise HTTPException(status_code=404, detail="Grievance not found.")

    grievance.verification_status = update.status
    grievance.verification_notes = update.notes.strip() if update.notes else None
    db.commit()
    db.refresh(grievance)

    return {
        "message": "Evidence verification updated successfully.",
        "grievance_id": grievance.id,
        "verification_status": grievance.verification_status,
        "verification_notes": grievance.verification_notes
    }


# ==========================================
# CITIZEN FEEDBACK
# ==========================================

@app.put(
    "/api/grievances/{grievance_id}/feedback"
)
def submit_feedback(

    grievance_id: int,

    feedback: schemas.GrievanceFeedback,

    db: Session = Depends(get_db)

):

    grievance = db.query(
        models.Grievance
    ).filter(

        models.Grievance.id == grievance_id

    ).first()


    if not grievance:

        raise HTTPException(

            status_code=404,

            detail="Grievance not found."

        )


    # ======================================
    # ONLY RESOLVED GRIEVANCES
    # ======================================

    if grievance.status != "Resolved":

        raise HTTPException(

            status_code=400,

            detail=(
                "Feedback can only be submitted "
                "after grievance resolution."
            )

        )


    # ======================================
    # VALIDATE RATING
    # ======================================

    if feedback.rating < 1 or feedback.rating > 5:

        raise HTTPException(

            status_code=400,

            detail="Rating must be between 1 and 5."

        )


    grievance.rating = feedback.rating

    grievance.feedback = feedback.feedback


    db.commit()

    db.refresh(grievance)


    return {

        "message":
            "Feedback submitted successfully.",

        "rating":
            grievance.rating

    }


# ==========================================
# DASHBOARD STATISTICS
# HIGHER AUTHORITY
# ==========================================

@app.get("/api/dashboard/stats")
def get_dashboard_stats(

    db: Session = Depends(get_db)

):

    grievances = db.query(
        models.Grievance
    ).all()


    total = len(grievances)


    pending = sum(

        1

        for grievance in grievances

        if grievance.status == "Pending"

    )


    assigned = sum(

        1

        for grievance in grievances

        if grievance.status == "Assigned"

    )


    in_progress = sum(

        1

        for grievance in grievances

        if grievance.status == "In Progress"

    )


    resolved = sum(

        1

        for grievance in grievances

        if grievance.status == "Resolved"

    )


    rejected = sum(

        1

        for grievance in grievances

        if grievance.status == "Rejected"

    )


    high_priority = sum(

        1

        for grievance in grievances

        if grievance.priority == "High"

    )


    return {

        "total": total,

        "pending": pending,

        "assigned": assigned,

        "in_progress": in_progress,

        "resolved": resolved,

        "rejected": rejected,

        "high_priority": high_priority

    }


# ==========================================
# DASHBOARD ANALYTICS
# ==========================================

@app.get("/api/dashboard/analytics")
def get_dashboard_analytics(

    db: Session = Depends(get_db)

):

    grievances = db.query(
        models.Grievance
    ).all()


    categories = Counter(

        grievance.category or "Uncategorized"

        for grievance in grievances

    )


    departments = Counter(

        grievance.department or "Unassigned"

        for grievance in grievances

    )


    priorities = Counter(

        grievance.priority or "Medium"

        for grievance in grievances

    )


    statuses = Counter(

        grievance.status

        for grievance in grievances

    )


    return {

        "total":
            len(grievances),

        "categories":
            dict(categories),

        "departments":
            dict(departments),

        "priorities":
            dict(priorities),

        "statuses":
            dict(statuses)

    }


# ==========================================
# AUTOMATED INSIGHTS
# ==========================================

@app.get("/api/dashboard/insights")
def get_dashboard_insights(

    db: Session = Depends(get_db)

):

    grievances = db.query(
        models.Grievance
    ).all()


    total = len(grievances)


    if total == 0:

        return {

            "insights": [

                "No grievances have been submitted yet."

            ]

        }


    categories = Counter(

        grievance.category or "Uncategorized"

        for grievance in grievances

    )


    departments = Counter(

        grievance.department or "Unassigned"

        for grievance in grievances

    )


    priorities = Counter(

        grievance.priority or "Medium"

        for grievance in grievances

    )


    statuses = Counter(

        grievance.status

        for grievance in grievances

    )


    insights = []


    # ======================================
    # MOST COMMON CATEGORY
    # ======================================

    most_common_category = (

        categories.most_common(1)[0]

    )


    insights.append(

        f"Most reported issue category is "
        f"{most_common_category[0]} with "
        f"{most_common_category[1]} grievance(s)."

    )


    # ======================================
    # BUSIEST DEPARTMENT
    # ======================================

    busiest_department = (

        departments.most_common(1)[0]

    )


    insights.append(

        f"Busiest department is "
        f"{busiest_department[0]} with "
        f"{busiest_department[1]} grievance(s)."

    )


    # ======================================
    # HIGH PRIORITY ALERT
    # ======================================

    high_priority = priorities.get(

        "High",

        0

    )


    if high_priority > 0:

        insights.append(

            f"{high_priority} high-priority "
            f"grievance(s) require immediate attention."

        )


    # ======================================
    # RESOLUTION RATE
    # ======================================

    resolved = statuses.get(

        "Resolved",

        0

    )


    resolution_rate = round(

        (resolved / total) * 100,

        1

    )


    insights.append(

        f"Current resolution rate is "
        f"{resolution_rate}%."

    )


    return {

        "insights":
            insights

    }


# ==========================================
# SERVE FRONTEND
# ==========================================

if FRONTEND_DIR.exists():

    app.mount(

        "/",

        StaticFiles(

            directory=str(FRONTEND_DIR),

            html=True

        ),

        name="frontend"

    )
