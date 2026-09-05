"""Database seed script — creates a safe synthetic clinical demonstration dataset.

Run via: python -m app.seed
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone

from sqlalchemy import select

from app.core.auth import hash_password
from app.core.database import Base, async_session_factory, engine
from app.models.analysis import (
    ChangeDirection,
    ClarificationQuestion,
    Comparison,
    ComparisonResult,
    Conflict,
    ConflictSeverity,
    ConflictStatus,
    Insight,
    Provenance,
    QuestionStatus,
    ReviewHistory,
    SourceType,
)
from app.models.patient import Patient, PatientIntake, Sex
from app.models.report import LabResult, ProcessingStatus, ReferenceStatus, Report
from app.models.user import User


async def seed_data() -> None:
    print("Beginning MedLens database seed...")

    # Create tables if not already present
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session_factory() as session:
        # Check if demo user already exists
        res = await session.execute(select(User).where(User.email == "doctor@medlens.health"))
        existing_user = res.scalar_one_or_none()

        if existing_user:
            print("Demo data already seeded (doctor@medlens.health exists). Ready!")
            return

        # 1. Create Demo Clinician User
        doctor = User(
            email="doctor@medlens.health",
            password_hash=hash_password("DemoPassword123!"),
            is_active=True,
        )
        session.add(doctor)
        await session.flush()
        print(f"Created Clinician User: {doctor.email} (ID: {doctor.id})")

        # 1b. Seed user revanthgatla6
        res_revanth = await session.execute(select(User).where(User.email.like("revanthgatla%")))
        if not res_revanth.scalar_one_or_none():
            revanth = User(
                email="revanthgatla6@gmail.com",
                password_hash=hash_password("DemoPassword123!"),
                is_active=True,
            )
            session.add(revanth)
            await session.flush()

        # 2. Create Demo Patient
        patient = Patient(
            owner_user_id=doctor.id,
            identifier="PT-2026-0842",
            name="Robert Martinez",
            age=54,
            sex=Sex.MALE,
        )
        session.add(patient)
        await session.flush()
        print(f"Created Demo Patient: {patient.name} (ID: {patient.id})")

        # 3. Create Patient Intake
        intake = PatientIntake(
            patient_id=patient.id,
            symptoms="Progressive fatigue for 6 weeks, mild dyspnea on exertion, bilateral lower extremity edema, intermittent dizziness.",
            existing_conditions="Type 2 Diabetes Mellitus (dx 2019), Essential Hypertension, Stage 2 Chronic Kidney Disease.",
            allergies="Lisinopril (angioedema, facial swelling), Amoxicillin (urticaria, rash), Metformin (severe GI distress).",
            medications="Amlodipine 10mg daily, Glipizide 5mg daily, Atorvastatin 40mg daily, Aspirin 81mg daily.",
            notes="Patient referred for comprehensive metabolic and hematologic workup. Strong history of ACE-inhibitor intolerance.",
        )
        session.add(intake)
        await session.flush()

        # 4. Previous Report (Feb 2026)
        raw_text_prev = """METROPOLITAN HEALTH DIAGNOSTICS
Patient Name: Robert Martinez
DOB: 1972-04-12 (Age: 53)  Sex: Male
Report Date: 2026-02-10
Accession: MHD-88219

COMPREHENSIVE METABOLIC & HEMATOLOGY PANEL
Hemoglobin: 13.4 g/dL (Reference: 13.0 - 17.0)
WBC: 7.4 x10^3/uL (Reference: 4.0 - 11.0)
Platelet Count: 215 x10^3/uL (Reference: 150 - 400)
Fasting Glucose: 118 mg/dL (Reference: 70 - 99) [HIGH]
HbA1c: 6.8 % (Reference: 4.0 - 5.6) [HIGH]
Serum Creatinine: 1.2 mg/dL (Reference: 0.7 - 1.3)
eGFR: 68 mL/min/1.73m2 (Reference: > 60)
Serum Potassium: 4.6 mEq/L (Reference: 3.5 - 5.0)
Total Cholesterol: 198 mg/dL (Reference: 125 - 200)
"""

        prev_report = Report(
            patient_id=patient.id,
            report_type="COMPREHENSIVE_METABOLIC_CBC",
            original_filename="Baseline_Lab_Panel_Feb2026.pdf",
            mime_type="application/pdf",
            report_date=datetime(2026, 2, 10, 9, 30, tzinfo=timezone.utc),
            source_name="Metropolitan Health Diagnostics",
            raw_text=raw_text_prev,
            processing_status=ProcessingStatus.VALIDATED,
            content_hash="hash_baseline_feb_2026",
            extraction_version="v1.0",
        )
        session.add(prev_report)
        await session.flush()

        prev_results_data = [
            ("Hemoglobin", "Hemoglobin", "13.4", 13.4, "g/dL", "13.0 - 17.0", 13.0, 17.0, ReferenceStatus.WITHIN),
            ("WBC", "White Blood Cell Count", "7.4", 7.4, "x10^3/uL", "4.0 - 11.0", 4.0, 11.0, ReferenceStatus.WITHIN),
            ("Platelet Count", "Platelet Count", "215", 215.0, "x10^3/uL", "150 - 400", 150.0, 400.0, ReferenceStatus.WITHIN),
            ("Fasting Glucose", "Fasting Glucose", "118", 118.0, "mg/dL", "70 - 99", 70.0, 99.0, ReferenceStatus.ABOVE),
            ("HbA1c", "Hemoglobin A1c", "6.8", 6.8, "%", "4.0 - 5.6", 4.0, 5.6, ReferenceStatus.ABOVE),
            ("Serum Creatinine", "Creatinine", "1.2", 1.2, "mg/dL", "0.7 - 1.3", 0.7, 1.3, ReferenceStatus.WITHIN),
            ("eGFR", "eGFR", "68", 68.0, "mL/min/1.73m2", "> 60", 60.0, None, ReferenceStatus.WITHIN),
            ("Serum Potassium", "Potassium", "4.6", 4.6, "mEq/L", "3.5 - 5.0", 3.5, 5.0, ReferenceStatus.WITHIN),
            ("Total Cholesterol", "Total Cholesterol", "198", 198.0, "mg/dL", "125 - 200", 125.0, 200.0, ReferenceStatus.WITHIN),
        ]

        for orig, canon, obs, val_num, unit, ref_txt, ref_l, ref_h, ref_st in prev_results_data:
            lr = LabResult(
                report_id=prev_report.id,
                original_name=orig,
                canonical_name=canon,
                observed_value=obs,
                value_numeric=val_num,
                unit=unit,
                reference_range_text=ref_txt,
                reference_low=ref_l,
                reference_high=ref_h,
                reference_status=ref_st,
                confidence=0.98,
                source_text=f"{orig}: {obs} {unit} (Reference: {ref_txt})",
                page_number=1,
                verified=True,
            )
            session.add(lr)
        await session.flush()

        # 5. Current Report (Aug 2026)
        raw_text_curr = """ADVANCED CLINICAL PATHOLOGY LABS
Patient Name: Robert Martinez
DOB: 1972-04-12 (Age: 54)  Sex: Male
Report Date: 2026-08-25
Accession: ACP-90412
Clinical Impression: Significant renal and glycemic shift. Consider ACE inhibitor (Lisinopril 10mg) for renal protection.

COMPREHENSIVE METABOLIC & HEMATOLOGY PANEL
Hemoglobin: 10.2 g/dL (Reference: 13.0 - 17.0) [LOW - ALERT]
WBC: 12.8 x10^3/uL (Reference: 4.0 - 11.0) [HIGH]
Platelet Count: 140 x10^3/uL (Reference: 150 - 400) [LOW]
Fasting Glucose: 168 mg/dL (Reference: 70 - 99) [HIGH]
HbA1c: 8.4 % (Reference: 4.0 - 5.6) [HIGH]
Serum Creatinine: 1.8 mg/dL (Reference: 0.7 - 1.3) [HIGH]
eGFR: 42 mL/min/1.73m2 (Reference: > 60) [LOW - DECLINING]
Serum Potassium: 5.6 mEq/L (Reference: 3.5 - 5.0) [HIGH - ALERT]
Total Cholesterol: 245 mg/dL (Reference: 125 - 200) [HIGH]
"""

        curr_report = Report(
            patient_id=patient.id,
            report_type="COMPREHENSIVE_METABOLIC_CBC",
            original_filename="Routine_Monitoring_Aug2026.pdf",
            mime_type="application/pdf",
            report_date=datetime(2026, 8, 25, 10, 15, tzinfo=timezone.utc),
            source_name="Advanced Clinical Pathology Labs",
            raw_text=raw_text_curr,
            processing_status=ProcessingStatus.REVIEW_REQUIRED,
            content_hash="hash_current_aug_2026",
            extraction_version="v1.0",
        )
        session.add(curr_report)
        await session.flush()

        curr_results_data = [
            ("Hemoglobin", "Hemoglobin", "10.2", 10.2, "g/dL", "13.0 - 17.0", 13.0, 17.0, ReferenceStatus.BELOW),
            ("WBC", "White Blood Cell Count", "12.8", 12.8, "x10^3/uL", "4.0 - 11.0", 4.0, 11.0, ReferenceStatus.ABOVE),
            ("Platelet Count", "Platelet Count", "140", 140.0, "x10^3/uL", "150 - 400", 150.0, 400.0, ReferenceStatus.BELOW),
            ("Fasting Glucose", "Fasting Glucose", "168", 168.0, "mg/dL", "70 - 99", 70.0, 99.0, ReferenceStatus.ABOVE),
            ("HbA1c", "Hemoglobin A1c", "8.4", 8.4, "%", "4.0 - 5.6", 4.0, 5.6, ReferenceStatus.ABOVE),
            ("Serum Creatinine", "Creatinine", "1.8", 1.8, "mg/dL", "0.7 - 1.3", 0.7, 1.3, ReferenceStatus.ABOVE),
            ("eGFR", "eGFR", "42", 42.0, "mL/min/1.73m2", "> 60", 60.0, None, ReferenceStatus.BELOW),
            ("Serum Potassium", "Potassium", "5.6", 5.6, "mEq/L", "3.5 - 5.0", 3.5, 5.0, ReferenceStatus.ABOVE),
            ("Total Cholesterol", "Total Cholesterol", "245", 245.0, "mg/dL", "125 - 200", 125.0, 200.0, ReferenceStatus.ABOVE),
        ]

        curr_lab_records = []
        for orig, canon, obs, val_num, unit, ref_txt, ref_l, ref_h, ref_st in curr_results_data:
            lr = LabResult(
                report_id=curr_report.id,
                original_name=orig,
                canonical_name=canon,
                observed_value=obs,
                value_numeric=val_num,
                unit=unit,
                reference_range_text=ref_txt,
                reference_low=ref_l,
                reference_high=ref_h,
                reference_status=ref_st,
                confidence=0.96,
                source_text=f"{orig}: {obs} {unit} (Reference: {ref_txt})",
                page_number=1,
                verified=False,
            )
            session.add(lr)
            curr_lab_records.append(lr)
        await session.flush()

        # 6. Provenance records
        for lr in curr_lab_records:
            prov = Provenance(
                entity_type="lab_result",
                entity_id=lr.id,
                source_type=SourceType.AI_EXTRACTED,
                source_report_id=curr_report.id,
                source_text=lr.source_text,
                page_number=1,
                location_hint="Table 1, Line " + str(lr.id),
                extraction_method="gemini-2.5-flash",
                confidence=0.96,
                verified=False,
            )
            session.add(prov)
        await session.flush()

        # 7. Conflicts
        c1 = Conflict(
            patient_id=patient.id,
            conflict_type="ALLERGY",
            severity=ConflictSeverity.HIGH,
            description="CRITICAL ALLERGY ALERT: Report notes recommend 'Consider ACE inhibitor (Lisinopril 10mg) for renal protection', directly conflicting with documented patient allergy: 'Lisinopril (angioedema, facial swelling)'.",
            source_a="Intake Documented Allergy: Lisinopril (angioedema)",
            source_b="Lab Note: 'Consider ACE inhibitor (Lisinopril 10mg)'",
            status=ConflictStatus.OPEN,
        )
        c2 = Conflict(
            patient_id=patient.id,
            conflict_type="MEDICATION",
            severity=ConflictSeverity.HIGH,
            description="HYPERKALEMIA & RENAL WARNING: Serum Potassium is elevated at 5.6 mEq/L with declining eGFR (42 mL/min). Concomitant ACE-i/ARB initiation or potassium-sparing agents are contraindicated without strict electrolyte monitoring.",
            source_a="Lab Result: Serum Potassium 5.6 mEq/L, eGFR 42 mL/min",
            source_b="Intake Active Regimen: Amlodipine, Glipizide, Atorvastatin",
            status=ConflictStatus.OPEN,
        )
        c3 = Conflict(
            patient_id=patient.id,
            conflict_type="MEDICATION",
            severity=ConflictSeverity.MEDIUM,
            description="HYPOGLYCEMIA RISK WITH IMPAIRED RENAL CLEARANCE: Active Glipizide therapy in the setting of acute kidney injury (eGFR reduced from 68 to 42 mL/min) increases systemic accumulation risk.",
            source_a="Intake: Glipizide 5mg daily",
            source_b="Lab Result: eGFR 42 mL/min",
            status=ConflictStatus.OPEN,
        )
        session.add_all([c1, c2, c3])
        await session.flush()

        # 8. Longitudinal Comparison
        comparison = Comparison(
            patient_id=patient.id,
            previous_report_id=prev_report.id,
            current_report_id=curr_report.id,
        )
        session.add(comparison)
        await session.flush()

        comp_items = [
            ("Hemoglobin", "13.4", "10.2", "g/dL", "g/dL", "13.0 - 17.0", "13.0 - 17.0", ChangeDirection.DECREASED, -3.2, -23.88),
            ("Creatinine", "1.2", "1.8", "mg/dL", "mg/dL", "0.7 - 1.3", "0.7 - 1.3", ChangeDirection.INCREASED, 0.6, 50.0),
            ("eGFR", "68", "42", "mL/min/1.73m2", "mL/min/1.73m2", "> 60", "> 60", ChangeDirection.DECREASED, -26.0, -38.24),
            ("Potassium", "4.6", "5.6", "mEq/L", "mEq/L", "3.5 - 5.0", "3.5 - 5.0", ChangeDirection.INCREASED, 1.0, 21.74),
            ("Fasting Glucose", "118", "168", "mg/dL", "mg/dL", "70 - 99", "70 - 99", ChangeDirection.INCREASED, 50.0, 42.37),
            ("Hemoglobin A1c", "6.8", "8.4", "%", "%", "4.0 - 5.6", "4.0 - 5.6", ChangeDirection.INCREASED, 1.6, 23.53),
            ("White Blood Cell Count", "7.4", "12.8", "x10^3/uL", "x10^3/uL", "4.0 - 11.0", "4.0 - 11.0", ChangeDirection.INCREASED, 5.4, 72.97),
            ("Platelet Count", "215", "140", "x10^3/uL", "x10^3/uL", "150 - 400", "150 - 400", ChangeDirection.DECREASED, -75.0, -34.88),
            ("Total Cholesterol", "198", "245", "mg/dL", "mg/dL", "125 - 200", "125 - 200", ChangeDirection.INCREASED, 47.0, 23.74),
        ]

        for canon, p_val, c_val, p_u, c_u, p_ref, c_ref, direction, delta, pct in comp_items:
            cr = ComparisonResult(
                comparison_id=comparison.id,
                canonical_name=canon,
                previous_value=p_val,
                current_value=c_val,
                previous_unit=p_u,
                current_unit=c_u,
                previous_reference_range=p_ref,
                current_reference_range=c_ref,
                direction=direction,
                absolute_change=delta,
                percentage_change=pct,
            )
            session.add(cr)
        await session.flush()

        # 9. Clarification Questions
        q1 = ClarificationQuestion(
            patient_id=patient.id,
            question="Has the patient taken non-steroidal anti-inflammatory drugs (NSAIDs) or nephrotoxic agents that could contribute to the acute eGFR decline from 68 to 42 mL/min?",
            reason="Investigate potential reversible cause for acute renal function deterioration.",
            priority=1,
            status=QuestionStatus.PENDING,
        )
        q2 = ClarificationQuestion(
            patient_id=patient.id,
            question="Was the fasting glucose of 168 mg/dL preceded by a confirmed 8-10 hour fast, and has the patient adhered to prescribed Glipizide therapy?",
            reason="Validate glycemic deterioration and rule out postprandial sampling artifact.",
            priority=2,
            status=QuestionStatus.PENDING,
        )
        q3 = ClarificationQuestion(
            patient_id=patient.id,
            question="Does the patient exhibit acute signs of infection (fever, dysuria, respiratory symptoms) correlating with leukocytosis (WBC 12.8 x10^3/uL)?",
            reason="Differentiate reactive leukocytosis from stress or medication response.",
            priority=3,
            status=QuestionStatus.PENDING,
        )
        session.add_all([q1, q2, q3])
        await session.flush()

        # 10. AI Clinical Insights
        insight = Insight(
            patient_id=patient.id,
            report_id=curr_report.id,
            summary=(
                "MedLens Clinical Intelligence Summary:\n\n"
                "1. Critical Safety Conflict: Report recommends ACE-inhibitor (Lisinopril 10mg) despite patient's documented life-threatening angioedema allergy to Lisinopril.\n\n"
                "2. Acute Renal Trajectory: Creatinine increased by +50.0% (1.2 -> 1.8 mg/dL) with eGFR dropping -38.2% (68 -> 42 mL/min), indicating transition to Stage 3b CKD or Acute Kidney Injury superimposed on CKD.\n\n"
                "3. Hyperkalemia & Electrolyte Imbalance: Potassium elevated at 5.6 mEq/L (+21.7% from 4.6 mEq/L). Requires immediate dietary potassium restriction and avoidance of potassium-sparing medications.\n\n"
                "4. Glycemic Deterioration: Fasting glucose jumped +42.4% (118 -> 168 mg/dL) and HbA1c rose from 6.8% to 8.4%, demonstrating uncontrolled diabetes.\n\n"
                "5. Hematologic Shift: New normocytic anemia with Hemoglobin down -23.9% (13.4 -> 10.2 g/dL), mild thrombocytopenia (140,000 /cumm), and leukocytosis (12,800 /cumm).\n\n"
                "DISCLAIMER: MedLens assists clinical evaluation through automated extraction and comparison. This summary is not medical advice. All decisions must be verified and authorized by a licensed healthcare provider."
            ),
            key_findings="• Lisinopril allergy conflict\n• eGFR drop to 42 mL/min\n• Potassium elevated at 5.6 mEq/L\n• HbA1c risen to 8.4%\n• New onset anemia (Hb 10.2 g/dL)",
            clarification_questions_text="NSAID use? Fasting duration confirmed? Active infection signs?",
            model_name="gemini-2.5-flash",
            prompt_version="v1.0",
        )
        session.add(insight)
        await session.flush()

        # 11. Review History
        review = ReviewHistory(
            patient_id=patient.id,
            entity_type="report",
            entity_id=curr_report.id,
            action="FLAGGED",
            previous_value="UPLOADED",
            new_value="REVIEW_REQUIRED",
            user_id=doctor.id,
        )
        session.add(review)
        await session.commit()

        print("MedLens synthetic demonstration database successfully seeded!")
        print("Login credentials:")
        print("  Email: doctor@medlens.health")
        print("  Password: DemoPassword123!")


if __name__ == "__main__":
    asyncio.run(seed_data())
