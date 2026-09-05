import React, { useState } from 'react';
import {
  CheckCircle2,
  AlertTriangle,
  XCircle,
  History,
  Download
} from 'lucide-react';
import { Report, ReviewHistoryItem } from '../types';
import { api } from '../api/client';


interface ReviewCenterViewProps {
  report: Report | null;
  reviewHistory: ReviewHistoryItem[];
  onSubmitReview: (reportId: number, data: { status: string; notes?: string }) => Promise<void>;
}

export const ReviewCenterView: React.FC<ReviewCenterViewProps> = ({
  report,
  reviewHistory,
  onSubmitReview,
}) => {
  const [reviewNote, setReviewNote] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isDownloadingPdf, setIsDownloadingPdf] = useState(false);

  if (!report) {
    return (
      <div className="glass-card" style={{ padding: '40px', textAlign: 'center' }}>
        <p style={{ color: 'var(--text-dim)' }}>Select a report to conduct human-in-the-loop clinician review.</p>
      </div>
    );
  }

  const handleDownloadPdf = async () => {
    if (!report?.patient_id) return;
    try {
      setIsDownloadingPdf(true);
      const blob = await api.downloadPatientReport(report.patient_id);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `medlens_report_patient_${report.patient_id}_${new Date().toISOString().slice(0, 10)}.pdf`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch (err: any) {
      alert(`Failed to download report PDF: ${err.message}`);
    } finally {
      setIsDownloadingPdf(false);
    }
  };

  const handleAction = async (status: 'ACCEPTED' | 'FLAGGED' | 'REJECTED') => {
    try {
      setIsSubmitting(true);
      await onSubmitReview(report.id, {
        status,
        notes: reviewNote || `Marked ${status} by clinician.`,
      });
      setReviewNote('');
    } finally {
      setIsSubmitting(false);
    }
  };

  const statusBadge =
    report.processing_status === 'VALIDATED'
      ? 'badge-normal'
      : report.processing_status === 'REVIEW_REQUIRED'
      ? 'badge-high'
      : report.processing_status === 'FAILED'
      ? 'badge-critical'
      : 'badge-purple';

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Header */}
      <div
        className="glass-card"
        style={{
          padding: '24px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          background: 'linear-gradient(135deg, rgba(15, 23, 42, 0.9), rgba(30, 41, 59, 0.6))',
          borderLeft: '4px solid #f59e0b',
          flexWrap: 'wrap',
          gap: '16px',
        }}
      >
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <h1 style={{ fontSize: '1.3rem', fontWeight: 800, color: 'var(--text-main)' }}>
              Clinician Review & Sign-Off Center
            </h1>
            <span className={`badge ${statusBadge}`}>
              Status: {report.processing_status}
            </span>
          </div>
          <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)', marginTop: '4px' }}>
            Human-in-the-loop governance: verify extraction fidelity, authorize findings, or flag anomalies.
          </p>
        </div>

        <button
          onClick={handleDownloadPdf}
          disabled={isDownloadingPdf}
          className="btn btn-secondary"
          style={{ fontSize: '0.84rem', padding: '8px 16px' }}
          title="Download PDF dossier for this patient"
        >
          <Download size={15} />
          <span>{isDownloadingPdf ? 'Generating PDF...' : 'Download Dossier PDF'}</span>
        </button>
      </div>

      {/* Action Card */}
      <div className="glass-card" style={{ padding: '24px' }}>
        <h2 style={{ fontSize: '1.05rem', fontWeight: 700, color: 'var(--text-main)', marginBottom: '14px' }}>
          Authorize or Flag Report #{report.id} ({report.original_filename || 'Diagnostic Panel'})
        </h2>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
          <div>
            <label style={{ display: 'block', fontSize: '0.78rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '6px' }}>
              Clinician Review Audit Note
            </label>
            <textarea
              value={reviewNote}
              onChange={(e) => setReviewNote(e.target.value)}
              className="form-textarea"
              rows={3}
              placeholder="e.g. Findings verified against primary laboratory source. Critical allergy conflict noted and discussed with patient."
            />
          </div>

          <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
            <button
              onClick={() => handleAction('ACCEPTED')}
              disabled={isSubmitting}
              className="btn btn-primary"
              style={{ background: 'linear-gradient(135deg, #10b981, #059669)', border: 'none', padding: '10px 20px' }}
            >
              <CheckCircle2 size={16} />
              <span>Approve & Authorize Report</span>
            </button>

            <button
              onClick={() => handleAction('FLAGGED')}
              disabled={isSubmitting}
              className="btn btn-secondary"
              style={{ background: 'rgba(245, 158, 11, 0.15)', borderColor: 'rgba(245, 158, 11, 0.3)', color: '#fde68a', padding: '10px 20px' }}
            >
              <AlertTriangle size={16} color="#f59e0b" />
              <span>Flag for Clinical Review</span>
            </button>

            <button
              onClick={() => handleAction('REJECTED')}
              disabled={isSubmitting}
              className="btn btn-danger"
              style={{ padding: '10px 20px' }}
            >
              <XCircle size={16} />
              <span>Reject Report</span>
            </button>
          </div>
        </div>
      </div>

      {/* Review Audit History */}
      <div className="glass-card" style={{ padding: '0', overflow: 'hidden' }}>
        <div style={{ padding: '16px 20px', borderBottom: '1px solid var(--border-dim)', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <History size={16} color="#38bdf8" />
          <h2 style={{ fontSize: '0.95rem', fontWeight: 700, color: 'var(--text-main)' }}>
            Immutable Clinician Audit Trail
          </h2>
        </div>

        {reviewHistory.length === 0 ? (
          <div style={{ padding: '32px', textAlign: 'center', color: 'var(--text-dim)', fontSize: '0.85rem' }}>
            No prior review history recorded for this patient.
          </div>
        ) : (
          <div className="data-table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Timestamp</th>
                  <th>Action</th>
                  <th>Clinician ID</th>
                  <th>Status Transition</th>
                  <th>Audit Notes</th>
                </tr>
              </thead>
              <tbody>
                {reviewHistory.map((item) => (
                  <tr key={item.id}>
                    <td style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                      {new Date(item.created_at).toLocaleString()}
                    </td>
                    <td>
                      <span className="badge badge-normal">{item.new_status || 'REVIEWED'}</span>
                    </td>
                    <td style={{ fontFamily: 'var(--font-mono)' }}>#{item.reviewer_user_id || item.id}</td>
                    <td style={{ fontSize: '0.8rem', color: 'var(--text-dim)' }}>
                      {item.previous_status || 'PENDING'} → <strong>{item.new_status}</strong>
                    </td>
                    <td style={{ color: 'var(--text-main)', fontSize: '0.85rem' }}>
                      {item.notes || 'No note attached.'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
