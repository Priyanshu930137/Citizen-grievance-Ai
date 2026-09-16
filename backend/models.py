# ==========================================
# CITIZEN CONNECT - DATABASE MODELS
# ==========================================

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime
)

from sqlalchemy.sql import func

from database import Base


# ==========================================
# USER MODEL
# ==========================================

class User(Base):

    __tablename__ = "users"


    # ======================================
    # USER ID
    # ======================================

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )


    # ======================================
    # BASIC DETAILS
    # ======================================

    name = Column(
        String(100),
        nullable=False
    )


    email = Column(
        String(150),
        unique=True,
        index=True,
        nullable=False
    )


    password = Column(
        String(255),
        nullable=False
    )


    # ======================================
    # USER ROLE
    #
    # citizen
    # authority
    # management
    # technician
    # ======================================

    role = Column(
        String(50),
        nullable=False,
        default="citizen"
    )


    # ======================================
    # DEPARTMENT
    #
    # Used for:
    # management
    # technician
    # ======================================

    department = Column(
        String(150),
        nullable=True
    )


    # ======================================
    # ACCOUNT CREATED DATE
    # ======================================

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )


# ==========================================
# GRIEVANCE MODEL
# ==========================================

class Grievance(Base):

    __tablename__ = "grievances"


    # ======================================
    # GRIEVANCE ID
    # ======================================

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )


    # ======================================
    # CITIZEN DETAILS
    # ======================================

    citizen_id = Column(
        Integer,
        nullable=False,
        index=True
    )


    citizen_name = Column(
        String(150),
        nullable=False
    )


    email = Column(
        String(150),
        nullable=False
    )


    phone = Column(
        String(20),
        nullable=True
    )


    # ======================================
    # GRIEVANCE DETAILS
    # ======================================

    subject = Column(
        String(255),
        nullable=False
    )


    description = Column(
        Text,
        nullable=False
    )

    image_url = Column(
    String(255),
    nullable=True
)

    # Evidence and duplicate-report tracking.
    image_hash = Column(String(64), nullable=True, index=True)
    image_metadata = Column(Text, nullable=True)
    parent_grievance_id = Column(Integer, nullable=True, index=True)
    is_duplicate = Column(Integer, nullable=False, default=0)
    duplicate_confidence = Column(Integer, nullable=True)
    report_count = Column(Integer, nullable=False, default=1)
    verification_status = Column(String(50), nullable=False, default="Pending Review")
    verification_notes = Column(Text, nullable=True)

    location = Column(
        String(255),
        nullable=False
    )


    # ======================================
    # AI ASSESSMENT
    # ======================================

    category = Column(
        String(100),
        nullable=False
    )


    department = Column(
        String(150),
        nullable=False
    )


    priority = Column(
        String(30),
        nullable=False,
        default="Medium"
    )


    ai_reason = Column(
        Text,
        nullable=True
    )


    # ======================================
    # GRIEVANCE STATUS
    #
    # Pending
    # Assigned
    # In Progress
    # Resolved
    # Rejected
    # ======================================

    status = Column(
        String(50),
        nullable=False,
        default="Pending"
    )


    # ======================================
    # TECHNICIAN ASSIGNMENT
    # ======================================

    assigned_technician_id = Column(
        Integer,
        nullable=True
    )


    assigned_technician_name = Column(
        String(150),
        nullable=True
    )


    # ======================================
    # TECHNICIAN DIAGNOSIS
    # ======================================

    diagnosis = Column(
        Text,
        nullable=True
    )


    # ======================================
    # RESOLUTION DETAILS
    # ======================================

    resolution_note = Column(
        Text,
        nullable=True
    )


    # ======================================
    # CITIZEN FEEDBACK
    # ======================================

    rating = Column(
        Integer,
        nullable=True
    )


    feedback = Column(
        Text,
        nullable=True
    )


    # ======================================
    # DATES
    # ======================================

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )


    updated_at = Column(
        DateTime(timezone=True),
        onupdate=func.now(),
        nullable=True
    )
