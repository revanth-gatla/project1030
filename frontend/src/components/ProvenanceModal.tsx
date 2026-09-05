import React from 'react';
import { X, Search, CheckCircle2, FileText, ShieldCheck } from 'lucide-react';
import { LabResult, Provenance } from '../types';

interface ProvenanceModalProps {
  labResult: LabResult | null;
  provenance: Provenance | null;
  onClose: () => void;
  onVerifyResult: (id: number) => void;
}

export const ProvenanceModal: React.FC<ProvenanceModalProps> = ({
  labResult,
  provenance,
  onClose,
  onVerifyResult,
}) => {
  if (!labResult) return null;

  const confidencePct = labResult.confidence
    ? Math.round(labResult.confidence * 100)
    : provenance?.confidence
    ? Math.round(provenance.confidence * 100)
    : null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()} style={{ padding: '24px' }}>
        {/* Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px', borderBottom: '1px solid var(--border-dim)', paddingBottom: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div style={{
              width: '36px',
              height: '36px',
              borderRadius: '8px',
              background: 'rgba(14, 165, 233, 0.15)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#38bdf8'
            }}>
              <Search size={18} />
            </div>
            <div>
              <h3 style={{ fontSize: '1.1rem', fontWeight: 700, color: 'var(--text-main)' }}>
                Source Traceability & Provenance
              </h3>
              <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                Deterministic audit trail linking extracted datum to source document text.
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            style={{ background: 'transparent', border: 'none', color: 'var(--text-dim)', cursor: 'pointer', padding: '4px' }}
          >
            <X size={20} />
          </button>
        </div>

        {/* Lab Result Details */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '12px', marginBottom: '20px' }}>
          <div style={{ background: 'rgba(15, 23, 42, 0.6)', padding: '12px', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-dim)' }}>
            <div style={{ fontSize: '0.72rem', color: 'var(--text-dim)', textTransform: 'uppercase' }}>Canonical Name</div>
            <div style={{ fontSize: '0.95rem', fontWeight: 700, color: 'var(--text-main)', marginTop: '4px' }}>{labResult.canonical_name}</div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Alias: {labResult.original_name}</div>
          </div>

          <div style={{ background: 'rgba(15, 23, 42, 0.6)', padding: '12px', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-dim)' }}>
            <div style={{ fontSize: '0.72rem', color: 'var(--text-dim)', textTransform: 'uppercase' }}>Extracted Value</div>
            <div style={{ fontSize: '1.1rem', fontWeight: 800, color: '#38bdf8', marginTop: '2px', fontFamily: 'var(--font-mono)' }}>
              {labResult.observed_value} {labResult.unit || ''}
            </div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
              Ref: {labResult.reference_range_text || '—'}
            </div>
          </div>

          <div style={{ background: 'rgba(15, 23, 42, 0.6)', padding: '12px', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-dim)' }}>
            <div style={{ fontSize: '0.72rem', color: 'var(--text-dim)', textTransform: 'uppercase' }}>Model Confidence</div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginTop: '4px' }}>
              <div style={{ fontSize: '1.1rem', fontWeight: 800, color: confidencePct && confidencePct > 90 ? '#10b981' : confidencePct !== null ? '#f59e0b' : 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                {confidencePct !== null ? `${confidencePct}%` : 'N/A'}
              </div>
              {confidencePct !== null && <ShieldCheck size={16} color="#10b981" />}
            </div>
            <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
              {confidencePct !== null ? 'Validated schema' : 'Not available'}
            </div>
          </div>
        </div>

        {/* Source Text Excerpt */}
        <div style={{ marginBottom: '20px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
            <span style={{ fontSize: '0.78rem', fontWeight: 700, textTransform: 'uppercase', color: 'var(--text-dim)', letterSpacing: '0.05em' }}>
              Original Report Text Snippet
            </span>
            {labResult.page_number && (
              <span className="badge badge-purple" style={{ fontSize: '0.7rem' }}>
                <FileText size={12} /> Page {labResult.page_number}
              </span>
            )}
          </div>
          <div style={{
            background: '#070b14',
            border: '1px solid rgba(56, 189, 248, 0.3)',
            borderRadius: 'var(--radius-md)',
            padding: '14px',
            fontFamily: 'var(--font-mono)',
            fontSize: '0.85rem',
            color: '#e2e8f0',
            lineHeight: '1.6',
            boxShadow: 'inset 0 2px 4px rgba(0,0,0,0.5)',
          }}>
            {labResult.source_text || provenance?.source_text_snippet || `Extracted: ${labResult.original_name} ${labResult.observed_value} ${labResult.unit || ''}`}
          </div>
        </div>

        {/* Verification Status & Action */}
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          background: labResult.verified ? 'rgba(16, 185, 129, 0.08)' : 'rgba(245, 158, 11, 0.08)',
          border: `1px solid ${labResult.verified ? 'rgba(16, 185, 129, 0.3)' : 'rgba(245, 158, 11, 0.3)'}`,
          borderRadius: 'var(--radius-md)',
          padding: '12px 16px',
        }}>
          <div>
            <div style={{ fontSize: '0.82rem', fontWeight: 600, color: labResult.verified ? '#86efac' : '#fde68a' }}>
              {labResult.verified ? 'Clinician Verified' : 'Pending Clinician Sign-Off'}
            </div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
              {labResult.verified
                ? 'This lab result has been reviewed and verified by a licensed clinician.'
                : 'Click verify to confirm that this extracted value matches source document.'}
            </div>
          </div>

          <button
            onClick={() => {
              onVerifyResult(labResult.id);
              onClose();
            }}
            className={`btn ${labResult.verified ? 'btn-secondary' : 'btn-primary'}`}
            style={{ fontSize: '0.8rem', padding: '6px 14px' }}
          >
            <CheckCircle2 size={15} />
            <span>{labResult.verified ? 'Re-Verify' : 'Verify Result'}</span>
          </button>
        </div>
      </div>
    </div>
  );
};
