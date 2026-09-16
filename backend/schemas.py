# ==========================================
# CITIZEN CONNECT - PYDANTIC SCHEMAS
# ==========================================

from pydantic import BaseModel, EmailStr, Field, field_validator

from typing import Literal, Optional


# ==========================================
# USER REGISTRATION
# ==========================================

class UserRegister(BaseModel):

    name: str = Field(min_length=2, max_length=100)

    email: EmailStr

    password: str = Field(min_length=6, max_length=128)

    role: str = "citizen"

    department: Optional[str] = None

    @field_validator("name", "password")
    @classmethod
    def cannot_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("This field cannot be blank.")
        return value.strip()


# ==========================================
# STAFF ACCOUNT PROVISIONING
# ==========================================

class StaffAccountCreate(BaseModel):

    # Credentials of the authority or management user creating the account.
    creator_email: EmailStr

    creator_password: str = Field(min_length=1, max_length=128)

    name: str = Field(min_length=2, max_length=100)

    email: EmailStr

    password: str = Field(min_length=6, max_length=128)

    role: Literal["management", "technician"]

    department: Optional[str] = None

    @field_validator("creator_password", "name", "password")
    @classmethod
    def staff_fields_cannot_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("This field cannot be blank.")
        return value.strip()


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


class GrievanceVerificationUpdate(BaseModel):

    status: Literal["Pending Review", "Verified", "Needs Review", "Rejected"]

    notes: Optional[str] = Field(default=None, max_length=1000)


# ==========================================
# CITIZEN FEEDBACK
# ==========================================

class GrievanceFeedback(BaseModel):

    rating: int

    feedback: Optional[str] = None
