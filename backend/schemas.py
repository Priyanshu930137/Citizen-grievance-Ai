# ==========================================
# CITIZEN CONNECT - PYDANTIC SCHEMAS
# ==========================================

from pydantic import BaseModel

from typing import Optional


# ==========================================
# USER REGISTRATION
# ==========================================

class UserRegister(BaseModel):

    name: str

    email: str

    password: str

    role: str = "citizen"

    department: Optional[str] = None


# ==========================================
# USER LOGIN
# ==========================================

class UserLogin(BaseModel):

    email: str

    password: str

    role: str


# ==========================================
# CREATE GRIEVANCE
# ==========================================

class GrievanceCreate(BaseModel):

    citizen_id: int

    citizen_name: str

    citizen_email: str

    citizen_phone: Optional[str] = None

    subject: str

    description: str

    location: str


# ==========================================
# ASSIGN TECHNICIAN
# ==========================================

class GrievanceAssign(BaseModel):

    technician_id: int


# ==========================================
# TECHNICIAN UPDATE
# ==========================================

class TechnicianUpdate(BaseModel):

    status: str

    diagnosis: Optional[str] = None

    resolution_note: Optional[str] = None


# ==========================================
# AUTHORITY STATUS UPDATE
# ==========================================

class GrievanceStatusUpdate(BaseModel):

    status: str


# ==========================================
# UPDATE DEPARTMENT
# ==========================================

class GrievanceDepartmentUpdate(BaseModel):

    department: str


# ==========================================
# UPDATE PRIORITY
# ==========================================

class GrievancePriorityUpdate(BaseModel):

    priority: str


# ==========================================
# CITIZEN FEEDBACK
# ==========================================

class GrievanceFeedback(BaseModel):

    rating: int

    feedback: Optional[str] = None