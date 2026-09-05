"""Deterministic parameter normalization using a dictionary lookup."""

from __future__ import annotations

# Built-in normalization dictionary — extensible via DB
_NORMALIZATION_MAP: dict[str, str] = {
    # Hemoglobin
    "hb": "Hemoglobin",
    "hgb": "Hemoglobin",
    "hemoglobin": "Hemoglobin",
    "haemoglobin": "Hemoglobin",
    "hb (hemoglobin)": "Hemoglobin",
    # White Blood Cells
    "wbc": "White Blood Cell Count",
    "white blood cells": "White Blood Cell Count",
    "white blood cell count": "White Blood Cell Count",
    "total wbc": "White Blood Cell Count",
    "total wbc count": "White Blood Cell Count",
    "leucocyte count": "White Blood Cell Count",
    "leukocyte count": "White Blood Cell Count",
    "tlc": "White Blood Cell Count",
    # Red Blood Cells
    "rbc": "Red Blood Cell Count",
    "red blood cells": "Red Blood Cell Count",
    "red blood cell count": "Red Blood Cell Count",
    "erythrocyte count": "Red Blood Cell Count",
    # Platelets
    "platelets": "Platelet Count",
    "platelet count": "Platelet Count",
    "plt": "Platelet Count",
    # Hematocrit
    "hct": "Hematocrit",
    "hematocrit": "Hematocrit",
    "haematocrit": "Hematocrit",
    "pcv": "Hematocrit",
    "packed cell volume": "Hematocrit",
    # MCV
    "mcv": "Mean Corpuscular Volume",
    "mean corpuscular volume": "Mean Corpuscular Volume",
    # MCH
    "mch": "Mean Corpuscular Hemoglobin",
    "mean corpuscular hemoglobin": "Mean Corpuscular Hemoglobin",
    # MCHC
    "mchc": "Mean Corpuscular Hemoglobin Concentration",
    # RDW
    "rdw": "Red Cell Distribution Width",
    "rdw-cv": "Red Cell Distribution Width",
    # ESR
    "esr": "Erythrocyte Sedimentation Rate",
    "erythrocyte sedimentation rate": "Erythrocyte Sedimentation Rate",
    # Blood Sugar
    "fbs": "Fasting Blood Sugar",
    "fasting blood sugar": "Fasting Blood Sugar",
    "fasting glucose": "Fasting Blood Sugar",
    "fasting blood glucose": "Fasting Blood Sugar",
    "rbs": "Random Blood Sugar",
    "random blood sugar": "Random Blood Sugar",
    "random glucose": "Random Blood Sugar",
    "ppbs": "Post-Prandial Blood Sugar",
    "post prandial blood sugar": "Post-Prandial Blood Sugar",
    "pp blood sugar": "Post-Prandial Blood Sugar",
    "hba1c": "Glycated Hemoglobin (HbA1c)",
    "glycated hemoglobin": "Glycated Hemoglobin (HbA1c)",
    "glycosylated hemoglobin": "Glycated Hemoglobin (HbA1c)",
    # Liver
    "sgot": "Aspartate Aminotransferase (AST)",
    "ast": "Aspartate Aminotransferase (AST)",
    "aspartate aminotransferase": "Aspartate Aminotransferase (AST)",
    "sgot/ast": "Aspartate Aminotransferase (AST)",
    "sgpt": "Alanine Aminotransferase (ALT)",
    "alt": "Alanine Aminotransferase (ALT)",
    "alanine aminotransferase": "Alanine Aminotransferase (ALT)",
    "sgpt /alt": "Alanine Aminotransferase (ALT)",
    "sgpt/alt": "Alanine Aminotransferase (ALT)",
    "alp": "Alkaline Phosphatase",
    "alkaline phosphatase": "Alkaline Phosphatase",
    "s.alkaline phosphatase": "Alkaline Phosphatase",
    "bilirubin": "Total Bilirubin",
    "total bilirubin": "Total Bilirubin",
    "s. bilirubin t": "Total Bilirubin",
    "s.bilirubin t": "Total Bilirubin",
    "bilirubin t": "Total Bilirubin",
    "direct bilirubin": "Direct Bilirubin",
    "s. bilirubin d": "Direct Bilirubin",
    "s.bilirubin d": "Direct Bilirubin",
    "bilirubin d": "Direct Bilirubin",
    "indirect bilirubin": "Indirect Bilirubin",
    "albumin": "Albumin",
    "s.albumin": "Albumin",
    "total protein": "Total Protein",
    "s.total protein": "Total Protein",
    "globulin": "Globulin",
    "a/g ratio": "Albumin/Globulin Ratio",
    "a:g ratio": "Albumin/Globulin Ratio",
    "ag ratio": "Albumin/Globulin Ratio",
    "ggt": "Gamma-Glutamyl Transferase (GGT)",
    "gamma gt": "Gamma-Glutamyl Transferase (GGT)",
    # Kidney
    "creatinine": "Creatinine",
    "serum creatinine": "Creatinine",
    "s.creatinine": "Creatinine",
    "urea": "Urea",
    "blood urea": "Urea",
    "bun": "Blood Urea Nitrogen",
    "blood urea nitrogen": "Blood Urea Nitrogen",
    "uric acid": "Uric Acid",
    "serum uric acid": "Uric Acid",
    "s.uric acid": "Uric Acid",
    "egfr": "Estimated Glomerular Filtration Rate",
    # Lipid Profile
    "cholesterol": "Total Cholesterol",
    "total cholesterol": "Total Cholesterol",
    "s.total cholesterol": "Total Cholesterol",
    "s.cholesterol": "Total Cholesterol",
    "hdl": "HDL Cholesterol",
    "hdl cholesterol": "HDL Cholesterol",
    "s.hdl": "HDL Cholesterol",
    "ldl": "LDL Cholesterol",
    "ldl cholesterol": "LDL Cholesterol",
    "s.ldl": "LDL Cholesterol",
    "triglycerides": "Triglycerides",
    "s.triglycerides": "Triglycerides",
    "tg": "Triglycerides",
    "vldl": "VLDL Cholesterol",
    "vldl cholesterol": "VLDL Cholesterol",
    "t.chol/hdl": "Total Cholesterol / HDL Ratio",
    "chol/hdl": "Total Cholesterol / HDL Ratio",
    "ldl/hdl": "LDL / HDL Ratio",
    # Thyroid
    "tsh": "Thyroid Stimulating Hormone",
    "thyroid stimulating hormone": "Thyroid Stimulating Hormone",
    "thyroid stimulating hormone (tsh)": "Thyroid Stimulating Hormone",
    "t3": "Triiodothyronine (T3)",
    "total t3": "Triiodothyronine (T3)",
    "t3 - total": "Triiodothyronine (T3)",
    "free t3": "Free Triiodothyronine (FT3)",
    "ft3": "Free Triiodothyronine (FT3)",
    "t4": "Thyroxine (T4)",
    "total t4": "Thyroxine (T4)",
    "t4 -total": "Thyroxine (T4)",
    "t4 - total": "Thyroxine (T4)",
    "free t4": "Free Thyroxine (FT4)",
    "ft4": "Free Thyroxine (FT4)",
    # Electrolytes & Minerals
    "sodium": "Sodium",
    "na": "Sodium",
    "na+": "Sodium",
    "potassium": "Potassium",
    "k": "Potassium",
    "k+": "Potassium",
    "chloride": "Chloride",
    "cl": "Chloride",
    "calcium": "Calcium",
    "s. calcium": "Calcium",
    "s.calcium": "Calcium",
    "serum calcium": "Calcium",
    "ca": "Calcium",
    "phosphorus": "Phosphorus",
    "magnesium": "Magnesium",
    "s.magnesium": "Magnesium",
    "serum magnesium": "Magnesium",
    "mg": "Magnesium",
    # Pancreatic & Enzymes
    "amylase": "Serum Amylase",
    "s.amylase": "Serum Amylase",
    "serum amylase": "Serum Amylase",
    "lipase": "Lipase",
    "serum lipase": "Lipase",
    # Differential Count
    "neutrophils": "Neutrophils",
    "lymphocytes": "Lymphocytes",
    "monocytes": "Monocytes",
    "eosinophils": "Eosinophils",
    "basophils": "Basophils",
    # Iron
    "iron": "Serum Iron",
    "serum iron": "Serum Iron",
    "tibc": "Total Iron Binding Capacity",
    "ferritin": "Ferritin",
    "serum ferritin": "Ferritin",
    # Vitamins
    "vitamin d": "Vitamin D",
    "vit d": "Vitamin D",
    "25-oh vitamin d": "Vitamin D",
    "vitamin b12": "Vitamin B12",
    "vit b12": "Vitamin B12",
    "folate": "Folate",
    "folic acid": "Folate",
    # Coagulation
    "pt": "Prothrombin Time",
    "prothrombin time": "Prothrombin Time",
    "inr": "International Normalized Ratio",
    "aptt": "Activated Partial Thromboplastin Time",
    # CRP
    "crp": "C-Reactive Protein",
    "c-reactive protein": "C-Reactive Protein",
    "hs-crp": "High-Sensitivity CRP",
}


def normalize_parameter_name(name: str) -> str:
    """Return canonical name for a parameter, or the original (title-cased) if unknown."""
    import re

    raw = name.strip()
    # Replace non-printable / replacement chars
    raw = re.sub(r"[\x00-\x1f\x7f-\x9f\ufffd]", " ", raw)
    key = raw.strip().lower()

    if key in _NORMALIZATION_MAP:
        return _NORMALIZATION_MAP[key]

    # Try stripping parenthesized abbreviation, e.g. "Hemoglobin (Hb)" -> "Hemoglobin"
    cleaned_key = re.sub(r"\s*\([^)]*\)", "", key).strip()
    if cleaned_key in _NORMALIZATION_MAP:
        return _NORMALIZATION_MAP[cleaned_key]

    # Try stripping leading "s." or "s " or "serum "
    stripped_prefix = re.sub(r"^(?:s\.\s*|s\s+|serum\s+)", "", cleaned_key).strip()
    if stripped_prefix in _NORMALIZATION_MAP:
        return _NORMALIZATION_MAP[stripped_prefix]

    return raw.strip().title()


def get_normalization_map() -> dict[str, str]:
    """Return a copy of the built-in normalization dictionary."""
    return dict(_NORMALIZATION_MAP)


# Metadata headers, field labels, and table header terms that must NEVER become lab parameters
DISALLOWED_PARAMETER_NAMES: set[str] = {
    "reference range",
    "reference ranges",
    "reference interval",
    "reference intervals",
    "biological reference interval",
    "biological reference intervals",
    "biological reference range",
    "biological reference ranges",
    "normal range",
    "normal ranges",
    "normal reference range",
    "expected range",
    "expected ranges",
    "reference",
    "ref range",
    "ref interval",
    "ref",
    "result",
    "results",
    "lab result",
    "lab results",
    "test result",
    "test results",
    "test name",
    "test names",
    "test / parameter",
    "test/parameter",
    "test parameter",
    "test",
    "tests",
    "parameter",
    "parameters",
    "parameter name",
    "investigation result",
    "investigation",
    "unit",
    "units",
    "value",
    "values",
    "observed value",
    "observed values",
    "flag",
    "flags",
    "status",
    "report status",
    "observation",
    "observations",
    "comment",
    "comments",
    "notes",
    "note",
    "interpretation",
    "method",
    "methodology",
    "specimen",
    "sample",
    "page",
    "cells/ul",
    "cells/µl",
    "cells/mm3",
    "cells/ml",
    # Reference interval classification tiers & cutoffs

    "desirable level",
    "desirable",
    "borderline",
    "borderline high",
    "borderline risk",
    "undesirable",
    "optimal",
    "near optimal",
    "high",
    "very high",
    "low",
    "low risk",
    "average risk",
    "moderate risk",
    "high risk",
    "adult",
    "adults",
    "child",
    "children",
    "male",
    "female",
}


def is_disallowed_parameter_name(name: str | None) -> bool:
    """Validate that candidate string is not a table header, metadata label, cutoff tier, or field name."""
    if not name:
        return True
    import re

    cleaned = name.strip().lower()
    cleaned = re.sub(r"[\x00-\x1f\x7f-\x9f\ufffd]", " ", cleaned)
    cleaned = cleaned.rstrip(":-. ").strip()
    if not cleaned:
        return True
    if cleaned in DISALLOWED_PARAMETER_NAMES:
        return True

    # Check if this is a classification tier / cutoff text e.g. "Borderline : 200 - 239", "Undesir Able", "Moder Ate Risk"
    compact = re.sub(r"[\s_\-]+", "", cleaned)
    if not compact:
        return True

    # Reject email addresses
    if "@" in cleaned and "." in cleaned:
        return True

    # Reject single or two-character noise symbols (unless recognized elements/short tests like T3, T4, Hb)
    if len(cleaned) <= 2 and cleaned not in ("t3", "t4", "hb", "na", "k", "cl", "fe", "cr", "ca", "mg", "p", "ph", "co", "zn", "cu", "bp"):
        return True

    # Reject common medications, dosages, and regimens
    if any(med in cleaned for med in (
        "amlodipine", "metformin", "lisinopril", "atorvastatin", "aspirin", "paracetamol",
        "once daily", "twice daily", "daily dose", "tablet", "capsule", "syrup", "oral",
        "mg daily", "active regimen",
    )):
        return True

    # Reject symptoms, clinical intake history, complaints
    if any(sym in cleaned for sym in (
        "fatigue", "thirst", "urination", "fever", "headache", "cough", "chest pain",
        "blurred vision", "nausea", "vomiting", "shortness of breath", "weight loss",
        "chief symptoms", "clinical notes", "existing diagnoses", "documented allergies",
        "symptoms have been present", "patient reports",
    )):
        return True

    # Reject administrative headers, departments, report metadata, and summary phrases
    if any(meta in cleaned for meta in (
        "clinical biochemistry", "diagnostic division", "managing clinician", "managing doctor",
        "intake & context", "official clinical record", "diagnostic reports", "reports on record",
        "processingstatus", "safety conflicts", "all findings reconciled", "indicating out-of-range",
        "generated", "verified", "pending", "document title", "source facility", "tests status",
        "level =", "ref =", "biomarker / test", "result value", "reference interval", "clinical intelligence",
    )):
        return True

    tier_compact_prefixes = (
        "desirable", "optimal", "borderline", "undesirable", "undesir",
        "risk", "moderaterisk", "moderate", "highrisk", "veryhigh",
        "lowrisk", "averagerisk", "borderlinerisk", "borderlinehigh", "nearoptimal",
    )
    for tc in tier_compact_prefixes:
        if compact == tc or compact.startswith(tc) or compact.endswith("risk"):
            return True

    tier_words = (
        "desirable", "optimal", "borderline", "undesirable", "risk",
        "adult", "near optimal", "very high", "moderate",
    )
    for tw in tier_words:
        if cleaned == tw or cleaned.startswith(f"{tw} ") or cleaned.startswith(f"{tw}:") or cleaned.startswith(f"{tw}-"):
            return True

    # Catch numeric prefixed strings that are actually cutoff values or tier lines
    # e.g. "110 U/L Adult", "158 mg/dL Desirable Level", "4.0 Low Risk", "1.9 Desirable Level"
    if re.match(r"^[<>]?\s*\d+[\d\.,/]*\s*(?:mg/dl|u/l|%|gm/dl|fl|pg)?\s*.*(?:desirable|optimal|borderline|risk|adult|undesirable)", cleaned, re.IGNORECASE):
        return True

    # Catch any string starting with a comparison operator or range indicator
    if re.match(r"^[<>]=?\s*\d+", cleaned):
        return True

    # Catch metadata phrases
    if any(phrase in cleaned for phrase in (
        "end of report", "please correlate", "consultant biochemist",
        "consultant pathologist", "test performed by", "lab address",
        "sample collection", "reporting date", "patient id", "op id",
        "investigation result", "biological reference",
    )):
        return True

    # Catch prefixed labels like "Reference Range: ..." or "Test Name: ..."
    for prefix in (
        "reference range",
        "reference ranges",
        "reference interval",
        "reference intervals",
        "biological reference interval",
        "biological reference range",
        "biological reference",
        "normal range",
        "normal ranges",
        "normal reference range",
        "expected range",
        "expected ranges",
        "ref range",
        "ref interval",
        "reference",
        "test / parameter",
        "test/parameter",
        "test parameter",
        "test name",
        "investigation result",
        "result",
        "results",
        "unit",
        "units",
        "value",
        "values",
        "observed value",
        "observation",
        "observations",
    ):
        if (
            cleaned == prefix
            or cleaned.startswith(f"{prefix} ")
            or cleaned.startswith(f"{prefix}:")
            or cleaned.startswith(f"{prefix}-")
            or cleaned.startswith(f"{prefix}=")
        ):
            return True
    return False


