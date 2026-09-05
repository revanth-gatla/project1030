import React, { useState } from 'react';
import {
  UserPlus,
  AlertOctagon,
  Pill,
  Heart,
  FileText,
  Save,
  CheckCircle2,
  ArrowRight,
  RotateCcw,
  ShieldCheck,
  Building2,
  UserCheck,
  Loader2
} from 'lucide-react';
import { Patient, PatientCreate } from '../types';

interface PatientIntakeViewProps {
  onSavePatient: (data: PatientCreate) => Promise<Patient>;
  onProceedToUpload: (patient: Patient) => void;
  onOpenWorkspace: (patient: Patient) => void;
}

export const PatientIntakeView: React.FC<PatientIntakeViewProps> = ({
  onSavePatient,
  onProceedToUpload,
  onOpenWorkspace,
}) => {
  // Form State
  const [name, setName] = useState('');
  const [identifier, setIdentifier] = useState('');
  const [age, setAge] = useState<string>('');
  const [sex, setSex] = useState<'MALE' | 'FEMALE' | 'OTHER' | 'UNKNOWN'>('MALE');
  const [symptoms, setSymptoms] = useState('');
  const [existingConditions, setExistingConditions] = useState('');
  const [allergies, setAllergies] = useState('');
  const [medications, setMedications] = useState('');
  const [notes, setNotes] = useState('');

  // UI State
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isSaved, setIsSaved] = useState(false);
  const [validationError, setValidationError] = useState<string | null>(null);
  const [createdPatient, setCreatedPatient] = useState<Patient | null>(null);

  const handleClear = () => {
    setName('');
    setIdentifier('');
    setAge('');
    setSex('MALE');
    setSymptoms('');
    setExistingConditions('');
    setAllergies('');
    setMedications('');
    setNotes('');
    setValidationError(null);
    setCreatedPatient(null);
    setIsSaved(false);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setValidationError(null);

    if (!name.trim()) {
      setValidationError('Patient full name is required.');
      return;
    }

    const parsedAge = age ? parseInt(age, 10) : undefined;
    if (age && (isNaN(parsedAge!) || parsedAge! < 0 || parsedAge! > 125)) {
      setValidationError('Please enter a valid age between 0 and 125.');
      return;
    }

    try {
      setIsSubmitting(true);
      const payload: PatientCreate = {
        name: name.trim(),
        identifier: identifier.trim() || undefined,
        age: parsedAge,
        sex,
        symptoms: symptoms.trim() || undefined,
        existing_conditions: existingConditions.trim() || undefined,
        allergies: allergies.trim() || undefined,
        medications: medications.trim() || undefined,
        notes: notes.trim() || undefined,
      };

      const saved = await onSavePatient(payload);
      setCreatedPatient(saved);
      setIsSaved(true);
    } catch (err: any) {
      setValidationError(err.message || 'Failed to save patient intake.');
      setIsSaved(false);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div style={{ maxWidth: '1000px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Workflow Step Banner */}
      <div
        className="glass-card"
        style={{
          padding: '20px 24px',
          background: 'linear-gradient(135deg, rgba(14, 165, 233, 0.12), rgba(99, 102, 241, 0.08))',
          borderLeft: '4px solid #0ea5e9',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '16px',
        }}
      >
        <div>
          <h1 style={{ fontSize: '1.35rem', fontWeight: 800, color: 'var(--text-main)', margin: 0 }}>
            New Patient Intake
          </h1>
          <p style={{ fontSize: '0.84rem', color: 'var(--text-muted)', marginTop: '4px', maxWidth: '680px' }}>
            Record patient demographics, acute symptoms, preexisting conditions, documented allergies, and current
            medications to establish the clinical context for report analysis.
          </p>
        </div>

        {/* Quick Helper Actions */}
        <div style={{ display: 'flex', gap: '10px' }}>
          <button
            type="button"
            onClick={handleClear}
            className="btn btn-secondary"
            style={{ fontSize: '0.82rem', padding: '8px 12px' }}
            title="Reset form fields"
          >
            <RotateCcw size={14} />
            <span>Clear</span>
          </button>
        </div>
      </div>

      {/* Success Confirmation Card (When Intake is Persisted) */}
      {createdPatient && (
        <div
          className="glass-card"
          style={{
            padding: '24px',
            background: 'linear-gradient(135deg, rgba(16, 185, 129, 0.15), rgba(15, 23, 42, 0.9))',
            border: '1px solid rgba(16, 185, 129, 0.4)',
            borderRadius: 'var(--radius-lg)',
            display: 'flex',
            flexDirection: 'column',
            gap: '16px',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '12px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <div
                style={{
                  width: '42px',
                  height: '42px',
                  borderRadius: '10px',
                  background: 'rgba(16, 185, 129, 0.2)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: '#10b981',
                }}
              >
                <CheckCircle2 size={24} />
              </div>
              <div>
                <h3 style={{ fontSize: '1.1rem', fontWeight: 800, color: '#86efac', margin: 0 }}>
                  Patient Record Created Successfully
                </h3>
                <div style={{ fontSize: '0.82rem', color: 'var(--text-muted)', marginTop: '2px' }}>
                  Profile established for <strong>{createdPatient.name}</strong> ({createdPatient.identifier || `ID #${createdPatient.id}`}) • Age: {createdPatient.age || 'N/A'} • Sex: {createdPatient.sex}
                </div>
              </div>
            </div>

            {/* Clinician Next Action Choices */}
            <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
              <button
                onClick={() => onProceedToUpload(createdPatient)}
                className="btn btn-primary"
                style={{ padding: '10px 18px', fontSize: '0.88rem' }}
              >
                <span>Add Medical Report</span>
                <ArrowRight size={16} />
              </button>

              <button
                onClick={() => onOpenWorkspace(createdPatient)}
                className="btn btn-secondary"
                style={{ padding: '10px 16px', fontSize: '0.88rem' }}
              >
                <UserCheck size={16} />
                <span>Open Patient Record</span>
              </button>

              <button
                onClick={handleClear}
                className="btn btn-secondary"
                style={{ padding: '10px 14px', fontSize: '0.88rem' }}
              >
                <UserPlus size={15} />
                <span>+ New Patient</span>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Validation Alert */}
      {validationError && (
        <div
          style={{
            background: 'var(--status-critical-bg)',
            border: '1px solid var(--status-critical-border)',
            padding: '12px 16px',
            borderRadius: 'var(--radius-md)',
            color: '#fda4af',
            display: 'flex',
            alignItems: 'center',
            gap: '10px',
            fontSize: '0.88rem',
          }}
        >
          <AlertOctagon size={18} />
          <span>{validationError}</span>
        </div>
      )}

      {/* Intake Entry Form */}
      <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
        {/* Core Demographics Card */}
        <div className="glass-card" style={{ padding: '24px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '18px' }}>
            <div
              style={{
                width: '32px',
                height: '32px',
                borderRadius: '8px',
                background: 'rgba(14, 165, 233, 0.15)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: '#38bdf8',
              }}
            >
              <Building2 size={18} />
            </div>
            <div>
              <h2 style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--text-main)', margin: 0 }}>
                Patient Demographics
              </h2>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>
                Required identification fields
              </div>
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '2fr 1.5fr 1fr 1.2fr', gap: '16px' }}>
            <div>
              <label style={{ display: 'block', fontSize: '0.78rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '6px' }}>
                Full Name <span style={{ color: '#f43f5e' }}>*</span>
              </label>
              <input
                type="text"
                value={name}
                onChange={(e) => { setName(e.target.value); if (isSaved) setIsSaved(false); }}
                placeholder="e.g. John Doe"
                className="form-input"
                required
              />
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '0.78rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '6px' }}>
                Patient ID / Identifier
              </label>
              <input
                type="text"
                value={identifier}
                onChange={(e) => { setIdentifier(e.target.value); if (isSaved) setIsSaved(false); }}
                placeholder="e.g. PT-10001"
                className="form-input"
              />
              <div style={{ fontSize: '0.72rem', color: 'var(--text-dim)', marginTop: '4px' }}>
                Optional — used to link this patient's medical records.
              </div>
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '0.78rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '6px' }}>
                Age <span style={{ color: '#f43f5e' }}>*</span>
              </label>
              <input
                type="number"
                value={age}
                onChange={(e) => { setAge(e.target.value); if (isSaved) setIsSaved(false); }}
                placeholder="54"
                min={0}
                max={125}
                className="form-input"
                required
              />
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '0.78rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '6px' }}>
                Biological Sex <span style={{ color: '#f43f5e' }}>*</span>
              </label>
              <select
                value={sex}
                onChange={(e) => { setSex(e.target.value as any); if (isSaved) setIsSaved(false); }}
                className="form-select"
                required
              >
                <option value="FEMALE">Female</option>
                <option value="MALE">Male</option>
                <option value="OTHER">Other</option>
                <option value="UNKNOWN">Unknown</option>
              </select>
            </div>
          </div>
        </div>

        {/* Safety-Critical Context Card (Allergies & Medications) */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
          {/* Documented Allergies (Critical Section) */}
          <div
            className="glass-card"
            style={{
              padding: '24px',
              borderTop: '3px solid #f43f5e',
              background: 'rgba(15, 23, 42, 0.85)',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '12px' }}>
              <div
                style={{
                  width: '32px',
                  height: '32px',
                  borderRadius: '8px',
                  background: 'rgba(244, 63, 94, 0.15)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: '#f43f5e',
                }}
              >
                <AlertOctagon size={18} />
              </div>
              <div>
                <h2 style={{ fontSize: '0.98rem', fontWeight: 700, color: '#fda4af', margin: 0 }}>
                  Documented Drug Allergies & Intolerances
                </h2>
                <div style={{ fontSize: '0.73rem', color: 'var(--text-dim)' }}>
                  Cross-referenced automatically against medications and lab profiles
                </div>
              </div>
            </div>

            <textarea
              value={allergies}
              onChange={(e) => { setAllergies(e.target.value); if (isSaved) setIsSaved(false); }}
              className="form-textarea"
              rows={4}
              placeholder="e.g. Lisinopril (angioedema), Penicillin (urticaria), Sulfa antibiotics"
              style={{ borderColor: allergies ? 'rgba(244, 63, 94, 0.3)' : undefined }}
            />
            <div style={{ fontSize: '0.72rem', color: 'var(--text-dim)', marginTop: '6px' }}>
              Separate multiple allergies with commas. Note known adverse reactions in parentheses.
            </div>
          </div>

          {/* Current Medications */}
          <div
            className="glass-card"
            style={{
              padding: '24px',
              borderTop: '3px solid #0ea5e9',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '12px' }}>
              <div
                style={{
                  width: '32px',
                  height: '32px',
                  borderRadius: '8px',
                  background: 'rgba(14, 165, 233, 0.15)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: '#38bdf8',
                }}
              >
                <Pill size={18} />
              </div>
              <div>
                <h2 style={{ fontSize: '0.98rem', fontWeight: 700, color: 'var(--text-main)', margin: 0 }}>
                  Active Current Medications
                </h2>
                <div style={{ fontSize: '0.73rem', color: 'var(--text-dim)' }}>
                  Reconciled against lab parameters (e.g. hyperkalemia, nephrotoxicity)
                </div>
              </div>
            </div>

            <textarea
              value={medications}
              onChange={(e) => { setMedications(e.target.value); if (isSaved) setIsSaved(false); }}
              className="form-textarea"
              rows={4}
              placeholder="e.g. Metformin 1000mg BID, Amlodipine 10mg daily, Furosemide 40mg daily"
            />
            <div style={{ fontSize: '0.72rem', color: 'var(--text-dim)', marginTop: '6px' }}>
              Include dosages, frequencies, and administration routes where available.
            </div>
          </div>
        </div>

        {/* Clinical History & Symptoms */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
          {/* Preexisting Conditions */}
          <div
            className="glass-card"
            style={{
              padding: '24px',
              borderTop: '3px solid #6366f1',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '12px' }}>
              <div
                style={{
                  width: '32px',
                  height: '32px',
                  borderRadius: '8px',
                  background: 'rgba(99, 102, 241, 0.15)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: '#818cf8',
                }}
              >
                <Heart size={18} />
              </div>
              <div>
                <h2 style={{ fontSize: '0.98rem', fontWeight: 700, color: 'var(--text-main)', margin: 0 }}>
                  Existing Conditions & Comorbidities
                </h2>
                <div style={{ fontSize: '0.73rem', color: 'var(--text-dim)' }}>
                  Informs clinical contextualization and abnormal thresholds
                </div>
              </div>
            </div>

            <textarea
              value={existingConditions}
              onChange={(e) => { setExistingConditions(e.target.value); if (isSaved) setIsSaved(false); }}
              className="form-textarea"
              rows={4}
              placeholder="e.g. Type 2 Diabetes Mellitus, Stage 3 CKD, Essential Hypertension"
            />
          </div>

          {/* Presenting Symptoms */}
          <div
            className="glass-card"
            style={{
              padding: '24px',
              borderTop: '3px solid #10b981',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '12px' }}>
              <div
                style={{
                  width: '32px',
                  height: '32px',
                  borderRadius: '8px',
                  background: 'rgba(16, 185, 129, 0.15)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: '#34d399',
                }}
              >
                <FileText size={18} />
              </div>
              <div>
                <h2 style={{ fontSize: '0.98rem', fontWeight: 700, color: 'var(--text-main)', margin: 0 }}>
                  Acute Symptoms & Presenting Complaints
                </h2>
                <div style={{ fontSize: '0.73rem', color: 'var(--text-dim)' }}>
                  Patient-reported symptoms, onset timeline, and severity
                </div>
              </div>
            </div>

            <textarea
              value={symptoms}
              onChange={(e) => { setSymptoms(e.target.value); if (isSaved) setIsSaved(false); }}
              className="form-textarea"
              rows={4}
              placeholder="e.g. Exertional dyspnea, progressive bilateral lower extremity edema (+2), fatigue"
            />
          </div>
        </div>

        {/* Additional Clinical Notes */}
        <div className="glass-card" style={{ padding: '24px' }}>
          <label style={{ display: 'block', fontSize: '0.82rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '8px' }}>
            Additional Relevant Information / Clinician Intake Notes
          </label>
          <textarea
            value={notes}
            onChange={(e) => { setNotes(e.target.value); if (isSaved) setIsSaved(false); }}
            className="form-textarea"
            rows={3}
            placeholder="e.g. Routine follow-up visit. Monitoring potassium and eGFR."
          />
        </div>

        {/* Bottom Success Confirmation Card (Immediately visible right where clinician clicked) */}
        {createdPatient && (
          <div
            className="glass-card"
            style={{
              padding: '18px 22px',
              background: 'linear-gradient(135deg, rgba(16, 185, 129, 0.16), rgba(15, 23, 42, 0.95))',
              border: '1px solid rgba(16, 185, 129, 0.45)',
              borderRadius: 'var(--radius-md)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              flexWrap: 'wrap',
              gap: '14px',
              boxShadow: '0 4px 20px rgba(16, 185, 129, 0.15)',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <div
                style={{
                  width: '38px',
                  height: '38px',
                  borderRadius: '10px',
                  background: 'rgba(16, 185, 129, 0.25)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: '#10b981',
                }}
              >
                <CheckCircle2 size={22} />
              </div>
              <div>
                <h3 style={{ fontSize: '1rem', fontWeight: 800, color: '#86efac', margin: 0 }}>
                  Saved — Patient Record Created Successfully
                </h3>
                <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '2px' }}>
                  Profile established for <strong>{createdPatient.name}</strong> ({createdPatient.identifier || `ID #${createdPatient.id}`}) • {createdPatient.age ? `${createdPatient.age} yo` : 'Age N/A'} • {createdPatient.sex}
                </div>
              </div>
            </div>

            <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
              <button
                type="button"
                onClick={() => onProceedToUpload(createdPatient)}
                className="btn btn-primary"
                style={{ padding: '8px 16px', fontSize: '0.85rem' }}
              >
                <span>Add Medical Report</span>
                <ArrowRight size={15} />
              </button>

              <button
                type="button"
                onClick={() => onOpenWorkspace(createdPatient)}
                className="btn btn-secondary"
                style={{ padding: '8px 14px', fontSize: '0.85rem' }}
              >
                <UserCheck size={15} />
                <span>Open Patient Record</span>
              </button>

              <button
                type="button"
                onClick={handleClear}
                className="btn btn-secondary"
                style={{ padding: '8px 12px', fontSize: '0.85rem' }}
              >
                <UserPlus size={14} />
                <span>+ New Patient</span>
              </button>
            </div>
          </div>
        )}

        {/* Submit Button Row */}
        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px', alignItems: 'center', flexWrap: 'wrap' }}>
          {isSaved ? (
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                color: '#34d399',
                fontSize: '0.86rem',
                fontWeight: 600,
                background: 'rgba(16, 185, 129, 0.12)',
                border: '1px solid rgba(16, 185, 129, 0.35)',
                padding: '8px 14px',
                borderRadius: 'var(--radius-sm)',
              }}
            >
              <CheckCircle2 size={16} color="#10b981" />
              <span>Saved to database</span>
            </div>
          ) : (
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.78rem', color: 'var(--text-dim)' }}>
              <ShieldCheck size={14} color="#10b981" />
              <span>Persisted directly to clinical database with audit trail</span>
            </div>
          )}

          <button
            type="submit"
            disabled={isSubmitting}
            className="btn"
            style={{
              padding: '12px 28px',
              fontSize: '0.92rem',
              fontWeight: 700,
              background: isSaved
                ? 'linear-gradient(135deg, #10b981, #059669)'
                : 'linear-gradient(135deg, #0ea5e9, #3b82f6)',
              borderColor: isSaved ? '#10b981' : '#0ea5e9',
              color: '#ffffff',
              boxShadow: isSaved
                ? '0 0 16px rgba(16, 185, 129, 0.4)'
                : '0 0 16px rgba(14, 165, 233, 0.3)',
              transition: 'all 0.25s ease',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              cursor: isSubmitting ? 'not-allowed' : 'pointer',
            }}
          >
            {isSubmitting ? (
              <>
                <Loader2 size={16} className="spin" />
                <span>Saving Patient...</span>
              </>
            ) : isSaved ? (
              <>
                <CheckCircle2 size={16} />
                <span>Saved</span>
              </>
            ) : (
              <>
                <Save size={16} />
                <span>Save Patient</span>
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
};
