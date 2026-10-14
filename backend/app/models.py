from sqlalchemy import Column, Integer, String, Float, Text
from .database import Base


# ============================================================
# USER MODEL
# ============================================================

class User(Base):
    __tablename__ = "users"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    name = Column(
        String(150),
        nullable=False
    )

    email = Column(
        String(200),
        unique=True,
        index=True,
        nullable=False
    )

    password = Column(
        String(200),
        nullable=False
    )


# ============================================================
# CLAIM MODEL
# ============================================================

class Claim(Base):
    __tablename__ = "claims"

    # --------------------------------------------------------
    # Claim identifiers
    # --------------------------------------------------------

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    claim_number = Column(
        String(50),
        unique=True,
        index=True
    )

    policy_number = Column(
        String(100)
    )

    # Logged-in user
    user_id = Column(
        Integer,
        nullable=True,
        index=True
    )

    # --------------------------------------------------------
    # Patient information
    # --------------------------------------------------------

    patient_name = Column(
        String(150),
        nullable=False
    )

    age = Column(
        Integer
    )

    # --------------------------------------------------------
    # Insurance information
    # --------------------------------------------------------

    insurance_type = Column(
        String(50),
        default="External"
    )

    insurance_company = Column(
        String(150)
    )

    # --------------------------------------------------------
    # Hospital and treatment
    # --------------------------------------------------------

    hospital_name = Column(
        String(200)
    )

    treatment = Column(
        String(200)
    )

    # --------------------------------------------------------
    # Claim amount
    # --------------------------------------------------------

    claim_amount = Column(
        Float
    )

    # --------------------------------------------------------
    # AI processing
    # --------------------------------------------------------

    eligibility_status = Column(
        String(50),
        default="Pending"
    )

    document_status = Column(
        String(50),
        default="Pending"
    )

    fraud_risk = Column(
        String(50),
        default="Pending"
    )

    assessment_status = Column(
        String(50),
        default="Pending"
    )

    # --------------------------------------------------------
    # Email / communication
    # --------------------------------------------------------

    email_status = Column(
        String(50),
        default="Pending"
    )

    # --------------------------------------------------------
    # Overall claim status
    # --------------------------------------------------------

    overall_status = Column(
        String(50),
        default="Submitted"
    )

    # --------------------------------------------------------
    # Remarks
    # --------------------------------------------------------

    remarks = Column(
        Text,
        nullable=True
    )