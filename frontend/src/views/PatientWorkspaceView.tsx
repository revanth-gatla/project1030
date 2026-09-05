import React, { useState } from 'react';
import {
  User,
  Heart,
  AlertOctagon,
  Pill,
  FileText,
  Edit2,
  Save,
  ShieldAlert,
  CheckCircle2,
  Table,
  FileUp,
  GitCompare,
  UserPlus,
  Check
} from 'lucide-react';
import { Patient, PatientIntake, Report, Conflict } from '../types';
import { TabType } from '../components/Sidebar';

interface PatientWorkspaceViewProps {
  patient: Patient | null;
  reports?: Report[];
  conflicts?: Conflict[];
  onUpdateIntake: (intake: PatientIntake) => Promise<void>;
  onNavigate?: (tab: TabType) => void;
  onSelectReport?: (reportId: number) => void;
  onNewIntake?: () => void;
}

export const PatientWorkspaceView: React.FC<PatientWorkspaceViewProps> = ({
  patient,
  reports = [],
  conflicts = [],
  onUpdateIntake,
  onNavigate,
  onSelectReport,
  onNewIntake,
}) => {
  const intake = patient?.intake || {};
  const [isEditing, setIsEditing] = useState(false);
  const [symptoms, setSymptoms] = useState(intake.symptoms || '');
  const [conditions, setConditions] = useState(intake.existing_conditions || '');
  const [allergies, setAllergies] = useState(intake.allergies || '');
  const [medications, setMedications] = useState(intake.medications || '');
  const [notes, setNotes] = useState(intake.notes || '');
  const [isSaving, setIsSaving] = useState(false);
  const [successMsg, setSuccessMsg] = useState(false);

  // Sync state if intake changes
  React.useEffect(() => {
    const cur = patient?.intake || {};
    setSymptoms(cur.symptoms || '');
    setConditions(cur.existing_conditions || '');
    setAllergies(cur.allergies || '');
    setMedications(cur.medications || '');
    setNotes(cur.notes || '');
  }, [patient?.intake]);

  if (!patient) {
    return (
      <div className="glass-card" style={{ padding: '60px 40px', textAlign: 'center' }}>
        <User size={48} style={{ opacity: 0.3, margin: '0 auto 16px auto', color: 'var(--text-dim)' }} />
        <h2 style={{ fontSize: '1.2rem', fontWeight: 700, color: 'var(--text-main)', marginBottom: '8px' }}>
          No Active Patient Selected
        </h2>
        <p style={{ color: 'var(--text-muted)', fontSize: '0.88rem', maxWidth: '460px', margin: '0 auto 20px auto' }}>
          Create a patient profile or select an existing patient from the top navigation bar.
        </p>
        {onNewIntake && (
          <button onClick={onNewIntake} className="btn btn-primary" style={{ margin: '0 auto' }}>
            <UserPlus size={16} />
            <span>+ New Patient</span>
          </button>
        )}
      </div>
    );
  }

  const handleSave = async () => {
    try {
      setIsSaving(true);
      await onUpdateIntake({
        symptoms,
        existing_conditions: conditions,
        allergies,
        medications,
        notes,
      });
      setIsEditing(false);
      setSuccessMsg(true);
      setTimeout(() => setSuccessMsg(false), 3000);
    } finally {
      setIsSaving(false);
    }
  };

  const activeConflicts = conflicts.filter((c) => c.status !== 'RESOLVED' && c.status !== 'DISMISSED');
  const allLabResults = reports.flatMap((r) => r.lab_results || []);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Workspace Header & Patient Demographics */}
      <div
        className="glass-card"
        style={{
          padding: '24px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          background: 'linear-gradient(135deg, rgba(15, 23, 42, 0.9), rgba(30, 41, 59, 0.6))',
          borderLeft: '4px solid #38bdf8',
          flexWrap: 'wrap',
          gap: '16px',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <div
            style={{
              width: '56px',
              height: '56px',
              borderRadius: '14px',
              background: 'linear-gradient(135deg, #0ea5e9, #3b82f6)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#ffffff',
              fontWeight: 800,
              fontSize: '1.5rem',
              boxShadow: '0 0 16px rgba(14, 165, 233, 0.3)',
            }}
          >
            {patient.name.charAt(0)}
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <h1 style={{ fontSize: '1.45rem', fontWeight: 800, color: 'var(--text-main)', margin: 0 }}>
                {patient.name}
              </h1>
              <span className="badge badge-normal">Structured Clinical Record</span>
              {activeConflicts.length > 0 && (
                <span className="badge badge-critical">
                  {activeConflicts.length} Active Conflict{activeConflicts.length > 1 ? 's' : ''}
                </span>
              )}
            </div>
            <div
              style={{
                display: 'flex',
                gap: '16px',
                fontSize: '0.82rem',
                color: 'var(--text-muted)',
                marginTop: '6px',
                flexWrap: 'wrap',
              }}
            >
              <span>
                Patient ID / Identifier:{' '}
                <strong style={{ color: 'var(--text-main)' }}>{patient.identifier || `PT-${patient.id}`}</strong>
              </span>
              <span>
                Age: <strong style={{ color: 'var(--text-main)' }}>{patient.age || 'N/A'}</strong>
              </span>
              <span>
                Sex: <strong style={{ color: 'var(--text-main)' }}>{patient.sex}</strong>
              </span>
              <span>
                Enrolled:{' '}
                <strong style={{ color: 'var(--text-main)' }}>
                  {new Date(patient.created_at).toLocaleDateString()}
                </strong>
              </span>
              <span>
                Reports:{' '}
                <strong style={{ color: 'var(--text-main)' }}>{reports.length} ingested</strong>
              </span>
            </div>
          </div>
        </div>

        {/* Action Controls */}
        <div style={{ display: 'flex', gap: '10px', alignItems: 'center', flexWrap: 'wrap' }}>
          {successMsg && (
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                color: '#10b981',
                fontSize: '0.82rem',
                fontWeight: 600,
              }}
            >
              <CheckCircle2 size={16} /> Intake Saved
            </div>
          )}

          {!isEditing ? (
            <button onClick={() => setIsEditing(true)} className="btn btn-secondary">
              <Edit2 size={15} />
              <span>Edit Intake</span>
            </button>
          ) : (
            <div style={{ display: 'flex', gap: '8px' }}>
              <button onClick={() => setIsEditing(false)} className="btn btn-secondary">
                Cancel
              </button>
              <button onClick={handleSave} disabled={isSaving} className="btn btn-primary">
                <Save size={15} />
                <span>{isSaving ? 'Saving...' : 'Save Intake'}</span>
              </button>
            </div>
          )}

          {onNavigate && (
            <button
              onClick={() => onNavigate('upload')}
              className="btn btn-primary"
              style={{ background: '#0ea5e9' }}
            >
              <FileUp size={15} />
              <span>+ Add Report</span>
            </button>
          )}
        </div>
      </div>

      {/* Patient Intake Sections (4-Card Clinical Grid) */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '20px' }}>
        {/* Documented Drug Allergies */}
        <div
          className="glass-card"
          style={{
            padding: '20px',
            borderTop: '3px solid #f43f5e',
            background: 'rgba(15, 23, 42, 0.85)',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '14px' }}>
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
              <h2 style={{ fontSize: '0.95rem', fontWeight: 700, color: '#fda4af', margin: 0 }}>
                Documented Allergies & Intolerances
              </h2>
              <div style={{ fontSize: '0.72rem', color: 'var(--text-dim)' }}>
                Cross-referenced during safety conflict analysis
              </div>
            </div>
          </div>

          {isEditing ? (
            <textarea
              value={allergies}
              onChange={(e) => setAllergies(e.target.value)}
              className="form-textarea"
              rows={4}
              placeholder="e.g. Lisinopril (angioedema), Penicillin (urticaria)"
            />
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {allergies ? (
                allergies
                  .split(/[,;\n]+/)
                  .filter(Boolean)
                  .map((a, i) => (
                    <div
                      key={i}
                      style={{
                        background: 'rgba(244, 63, 94, 0.08)',
                        border: '1px solid rgba(244, 63, 94, 0.3)',
                        borderRadius: 'var(--radius-md)',
                        padding: '8px 12px',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '8px',
                        color: '#fecdd3',
                        fontSize: '0.85rem',
                        fontWeight: 600,
                      }}
                    >
                      <ShieldAlert size={15} color="#f43f5e" />
                      <span>{a.trim()}</span>
                    </div>
                  ))
              ) : (
                <div style={{ fontSize: '0.85rem', color: 'var(--text-dim)', fontStyle: 'italic' }}>
                  No known drug allergies recorded.
                </div>
              )}
            </div>
          )}
        </div>

        {/* Current Active Medications */}
        <div
          className="glass-card"
          style={{
            padding: '20px',
            borderTop: '3px solid #0ea5e9',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '14px' }}>
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
              <h2 style={{ fontSize: '0.95rem', fontWeight: 700, color: 'var(--text-main)', margin: 0 }}>
                Active Medications
              </h2>
              <div style={{ fontSize: '0.72rem', color: 'var(--text-dim)' }}>
                Reconciled against lab parameters & contraindications
              </div>
            </div>
          </div>

          {isEditing ? (
            <textarea
              value={medications}
              onChange={(e) => setMedications(e.target.value)}
              className="form-textarea"
              rows={4}
              placeholder="e.g. Amlodipine 10mg daily, Metformin 1000mg BID"
            />
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {medications ? (
                medications
                  .split(/[,;\n]+/)
                  .filter(Boolean)
                  .map((m, i) => (
                    <div
                      key={i}
                      style={{
                        background: 'rgba(14, 165, 233, 0.08)',
                        border: '1px solid rgba(14, 165, 233, 0.25)',
                        borderRadius: 'var(--radius-md)',
                        padding: '8px 12px',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '8px',
                        color: '#bae6fd',
                        fontSize: '0.85rem',
                        fontWeight: 500,
                      }}
                    >
                      <Pill size={14} color="#38bdf8" />
                      <span>{m.trim()}</span>
                    </div>
                  ))
              ) : (
                <div style={{ fontSize: '0.85rem', color: 'var(--text-dim)', fontStyle: 'italic' }}>
                  No active medications recorded.
                </div>
              )}
            </div>
          )}
        </div>

        {/* Existing Conditions */}
        <div
          className="glass-card"
          style={{
            padding: '20px',
            borderTop: '3px solid #6366f1',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '14px' }}>
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
              <h2 style={{ fontSize: '0.95rem', fontWeight: 700, color: 'var(--text-main)', margin: 0 }}>
                Existing Conditions & Comorbidities
              </h2>
              <div style={{ fontSize: '0.72rem', color: 'var(--text-dim)' }}>
                Baseline clinical context for reference range evaluation
              </div>
            </div>
          </div>

          {isEditing ? (
            <textarea
              value={conditions}
              onChange={(e) => setConditions(e.target.value)}
              className="form-textarea"
              rows={4}
              placeholder="e.g. Type 2 Diabetes, Essential Hypertension, CKD"
            />
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {conditions ? (
                conditions
                  .split(/[,;\n]+/)
                  .filter(Boolean)
                  .map((c, i) => (
                    <div
                      key={i}
                      style={{
                        background: 'rgba(99, 102, 241, 0.08)',
                        border: '1px solid rgba(99, 102, 241, 0.25)',
                        borderRadius: 'var(--radius-md)',
                        padding: '8px 12px',
                        color: '#c7d2fe',
                        fontSize: '0.85rem',
                        fontWeight: 500,
                      }}
                    >
                      • {c.trim()}
                    </div>
                  ))
              ) : (
                <div style={{ fontSize: '0.85rem', color: 'var(--text-dim)', fontStyle: 'italic' }}>
                  No preexisting conditions listed.
                </div>
              )}
            </div>
          )}
        </div>

        {/* Symptoms & Notes */}
        <div
          className="glass-card"
          style={{
            padding: '20px',
            borderTop: '3px solid #10b981',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '14px' }}>
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
              <h2 style={{ fontSize: '0.95rem', fontWeight: 700, color: 'var(--text-main)', margin: 0 }}>
                Presenting Symptoms & Intake Notes
              </h2>
              <div style={{ fontSize: '0.72rem', color: 'var(--text-dim)' }}>
                Acute presentation & clinician observations
              </div>
            </div>
          </div>

          {isEditing ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              <div>
                <label style={{ display: 'block', fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '4px' }}>
                  Symptoms
                </label>
                <textarea
                  value={symptoms}
                  onChange={(e) => setSymptoms(e.target.value)}
                  className="form-textarea"
                  rows={2}
                />
              </div>
              <div>
                <label style={{ display: 'block', fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '4px' }}>
                  Clinical Notes
                </label>
                <textarea
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  className="form-textarea"
                  rows={2}
                />
              </div>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', fontSize: '0.85rem', color: '#cbd5e1' }}>
              <div>
                <strong style={{ color: 'var(--text-main)' }}>Symptoms:</strong>
                <p style={{ marginTop: '2px', color: 'var(--text-muted)' }}>{symptoms || 'None reported.'}</p>
              </div>
              <div>
                <strong style={{ color: 'var(--text-main)' }}>Clinician Notes:</strong>
                <p style={{ marginTop: '2px', color: 'var(--text-muted)' }}>{notes || 'No general notes recorded.'}</p>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Ingested Medical Reports List */}
      <div className="glass-card" style={{ padding: '0', overflow: 'hidden' }}>
        <div
          style={{
            padding: '16px 20px',
            borderBottom: '1px solid var(--border-dim)',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <FileText size={18} color="#38bdf8" />
            <h2 style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--text-main)', margin: 0 }}>
              Ingested Medical Reports ({reports.length})
            </h2>
          </div>

          {onNavigate && (
            <div style={{ display: 'flex', gap: '8px' }}>
              {reports.length >= 2 && (
                <button
                  onClick={() => onNavigate('comparison')}
                  className="btn btn-secondary"
                  style={{ fontSize: '0.78rem', padding: '5px 12px' }}
                >
                  <GitCompare size={14} />
                  <span>Compare Trajectory</span>
                </button>
              )}
              <button
                onClick={() => onNavigate('upload')}
                className="btn btn-primary"
                style={{ fontSize: '0.78rem', padding: '5px 12px' }}
              >
                <FileUp size={14} />
                <span>+ Upload Report</span>
              </button>
            </div>
          )}
        </div>

        {reports.length === 0 ? (
          <div style={{ padding: '40px', textAlign: 'center', color: 'var(--text-dim)' }}>
            <FileUp size={36} style={{ opacity: 0.4, margin: '0 auto 12px auto' }} />
            <div>No medical reports ingested yet for this patient.</div>
            <div style={{ fontSize: '0.8rem', marginTop: '6px' }}>
              Upload or paste a medical report to trigger parameter extraction and analysis.
            </div>
          </div>
        ) : (
          <div className="data-table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Report Identifier</th>
                  <th>Date</th>
                  <th>Facility / Source</th>
                  <th>Extracted Labs</th>
                  <th>Status</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {reports.map((rep) => (
                  <tr key={rep.id}>
                    <td>
                      <div style={{ fontWeight: 700, color: 'var(--text-main)' }}>
                        {rep.original_filename || `Report #${rep.id}`}
                      </div>
                      <div style={{ fontSize: '0.7rem', color: 'var(--text-dim)' }}>
                        Type: {rep.report_type || 'Diagnostic Panel'}
                      </div>
                    </td>
                    <td style={{ fontSize: '0.82rem' }}>
                      {rep.report_date ? new Date(rep.report_date).toLocaleDateString() : 'N/A'}
                    </td>
                    <td style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>
                      {rep.source_name || 'Clinical Pathology Labs'}
                    </td>
                    <td>
                      <span className="badge badge-normal" style={{ fontWeight: 700 }}>
                        {rep.lab_results?.length || 0} biomarkers
                      </span>
                    </td>
                    <td>
                      <span
                        className={`badge ${
                          rep.processing_status === 'VALIDATED'
                            ? 'badge-normal'
                            : rep.processing_status === 'REVIEW_REQUIRED'
                            ? 'badge-critical'
                            : 'badge-high'
                        }`}
                      >
                        {rep.processing_status}
                      </span>
                    </td>
                    <td>
                      <div style={{ display: 'flex', gap: '8px' }}>
                        <button
                          onClick={() => {
                            if (onSelectReport) onSelectReport(rep.id);
                            if (onNavigate) onNavigate('results');
                          }}
                          className="btn btn-secondary"
                          style={{ fontSize: '0.75rem', padding: '4px 10px' }}
                        >
                          <Table size={13} />
                          <span>View Labs</span>
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Extracted Biomarker Quick Summary */}
      {allLabResults.length > 0 && (
        <div className="glass-card" style={{ padding: '0', overflow: 'hidden' }}>
          <div
            style={{
              padding: '16px 20px',
              borderBottom: '1px solid var(--border-dim)',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Table size={18} color="#10b981" />
              <h2 style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--text-main)', margin: 0 }}>
                Recent Biomarker Measurements ({allLabResults.length})
              </h2>
            </div>
            {onNavigate && (
              <button
                onClick={() => onNavigate('results')}
                className="btn btn-secondary"
                style={{ fontSize: '0.78rem', padding: '4px 10px' }}
              >
                Open Full Lab Table →
              </button>
            )}
          </div>

          <div className="data-table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Biomarker</th>
                  <th>Observed Value</th>
                  <th>Reference Range</th>
                  <th>Classification</th>
                  <th>Verification</th>
                </tr>
              </thead>
              <tbody>
                {allLabResults.slice(0, 8).map((res) => (
                  <tr key={res.id}>
                    <td style={{ fontWeight: 700, color: 'var(--text-main)' }}>
                      {res.canonical_name || res.original_name}
                    </td>
                    <td style={{ fontFamily: 'var(--font-mono)', fontWeight: 700, color: 'var(--text-main)' }}>
                      {res.observed_value} {res.unit || ''}
                    </td>
                    <td style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>
                      {res.reference_range_text ||
                        (res.reference_low !== null && res.reference_high !== null
                          ? `${res.reference_low} - ${res.reference_high} ${res.unit || ''}`
                          : 'N/A')}
                    </td>
                    <td>
                      <span
                        className={`badge ${
                          res.reference_status === 'ABOVE' || res.reference_status === 'HIGH'
                            ? 'badge-high'
                            : res.reference_status === 'BELOW' || res.reference_status === 'LOW'
                            ? 'badge-low'
                            : res.reference_status === 'WITHIN'
                            ? 'badge-normal'
                            : ''
                        }`}
                      >
                        {res.reference_status}
                      </span>
                    </td>
                    <td>
                      {res.verified ? (
                        <span className="badge badge-normal" style={{ fontSize: '0.7rem' }}>
                          <Check size={11} /> Verified
                        </span>
                      ) : (
                        <span style={{ fontSize: '0.72rem', color: 'var(--text-dim)' }}>Pending Review</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};
