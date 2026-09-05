"""Model registry — import all models so Alembic sees them."""

from app.models.analysis import (  # noqa: F401
    ClarificationQuestion,
    Comparison,
    ComparisonResult,
    Conflict,
    Insight,
    NormalizationDictionary,
    Provenance,
    ReviewHistory,
)
from app.models.patient import Patient, PatientIntake  # noqa: F401
from app.models.report import LabResult, Report  # noqa: F401
from app.models.user import User  # noqa: F401
