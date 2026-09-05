import React, { useState } from 'react';
import { X, Edit3, Save, AlertCircle } from 'lucide-react';
import { LabResult } from '../types';

interface EditLabResultModalProps {
  labResult: LabResult | null;
  onClose: () => void;
  onSave: (id: number, update: Partial<LabResult>) => Promise<void>;
}

export const EditLabResultModal: React.FC<EditLabResultModalProps> = ({
  labResult,
  onClose,
  onSave,
}) => {
  const [observedValue, setObservedValue] = useState(labResult?.observed_value || '');
  const [unit, setUnit] = useState(labResult?.unit || '');
  const [referenceRangeText, setReferenceRangeText] = useState(labResult?.reference_range_text || '');
  const [auditNote, setAuditNote] = useState('');
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  React.useEffect(() => {
    if (labResult) {
      setObservedValue(labResult.observed_value || '');
      setUnit(labResult.unit || '');
      setReferenceRangeText(labResult.reference_range_text || '');
    }
  }, [labResult]);

  if (!labResult) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!observedValue.trim()) {
      setError('Observed value cannot be empty.');
      return;
    }

    try {
      setIsSaving(true);
      setError(null);
      await onSave(labResult.id, {
        observed_value: observedValue,
        unit: unit,
        reference_range_text: referenceRangeText,
        verified: true,
      });
      onClose();
    } catch (err: any) {
      setError(err.message || 'Failed to save correction.');
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()} style={{ padding: '24px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px', borderBottom: '1px solid var(--border-dim)', paddingBottom: '14px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div style={{
              width: '36px',
              height: '36px',
              borderRadius: '8px',
              background: 'rgba(56, 189, 248, 0.15)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#38bdf8'
            }}>
              <Edit3 size={18} />
            </div>
            <div>
              <h3 style={{ fontSize: '1.1rem', fontWeight: 700, color: 'var(--text-main)' }}>
                Correct Lab Value & Audit Note
              </h3>
              <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                {labResult.canonical_name} ({labResult.original_name})
              </p>
            </div>
          </div>
          <button onClick={onClose} style={{ background: 'transparent', border: 'none', color: 'var(--text-dim)', cursor: 'pointer' }}>
            <X size={20} />
          </button>
        </div>

        {error && (
          <div style={{ background: 'var(--status-critical-bg)', border: '1px solid var(--status-critical-border)', padding: '10px 14px', borderRadius: 'var(--radius-md)', color: '#fca5a5', fontSize: '0.82rem', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <AlertCircle size={16} />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div>
            <label style={{ display: 'block', fontSize: '0.78rem', color: 'var(--text-muted)', marginBottom: '6px', fontWeight: 600 }}>
              Observed Value *
            </label>
            <input
              type="text"
              value={observedValue}
              onChange={(e) => setObservedValue(e.target.value)}
              className="form-input"
              required
            />
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
            <div>
              <label style={{ display: 'block', fontSize: '0.78rem', color: 'var(--text-muted)', marginBottom: '6px', fontWeight: 600 }}>
                Unit
              </label>
              <input
                type="text"
                value={unit}
                onChange={(e) => setUnit(e.target.value)}
                className="form-input"
                placeholder="e.g. g/dL, mg/dL"
              />
            </div>
            <div>
              <label style={{ display: 'block', fontSize: '0.78rem', color: 'var(--text-muted)', marginBottom: '6px', fontWeight: 600 }}>
                Reference Range
              </label>
              <input
                type="text"
                value={referenceRangeText}
                onChange={(e) => setReferenceRangeText(e.target.value)}
                className="form-input"
                placeholder="e.g. 13.0 - 17.0"
              />
            </div>
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '0.78rem', color: 'var(--text-muted)', marginBottom: '6px', fontWeight: 600 }}>
              Clinical Audit Note (Reason for adjustment)
            </label>
            <textarea
              value={auditNote}
              onChange={(e) => setAuditNote(e.target.value)}
              className="form-textarea"
              rows={3}
              placeholder="e.g. Verified with primary lab printout; manual entry adjustment per hematology consult."
            />
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '10px' }}>
            <button type="button" onClick={onClose} className="btn btn-secondary">
              Cancel
            </button>
            <button type="submit" disabled={isSaving} className="btn btn-primary">
              <Save size={16} />
              <span>{isSaving ? 'Saving...' : 'Save & Mark Verified'}</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
