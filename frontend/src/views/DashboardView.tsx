import React, { useState } from 'react';
import {
  FileText,
  AlertTriangle,
  ClipboardCheck,
  HelpCircle,
  ArrowRight,
  PlusCircle,
  TrendingUp,
  ShieldCheck,
  Activity,
  UserPlus,
  Download,
  Check,
  BrainCircuit,
  Users
} from 'lucide-react';
import { Patient, Report, Conflict, ClarificationQuestion } from '../types';
import { TabType } from '../components/Sidebar';
import { api } from '../api/client';

interface DashboardViewProps {
  patient: Patient | null;
  reports: Report[];
  conflicts: Conflict[];
  questions: ClarificationQuestion[];
  onNavigate: (tab: TabType) => void;
  onSelectReport: (reportId: number) => void;
}

export const DashboardView: React.FC<DashboardViewProps> = ({
  patient,
  reports,
  conflicts,
  questions,
  onNavigate,
  onSelectReport,
}) => {
  const [isDownloadingPdf, setIsDownloadingPdf] = useState(false);
  const [pdfSuccess, setPdfSuccess] = useState(false);

  const activeConflicts = conflicts.filter((c) => c.status === 'OPEN' || c.status === 'ACKNOWLEDGED');
  const criticalConflicts = activeConflicts.filter((c) => c.severity === 'CRITICAL' || c.severity === 'HIGH');
  const pendingQuestions = questions.filter((q) => !q.answered);
  const latestReport = reports[0];

  const handleDownloadPdf = async () => {
    if (!patient) return;
    try {
      setIsDownloadingPdf(true);
      const blob = await api.downloadPatientReport(patient.id);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `medlens_report_${patient.identifier || `PAT-${patient.id}`}_${new Date().toISOString().slice(0, 10)}.pdf`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
      setPdfSuccess(true);
      setTimeout(() => setPdfSuccess(false), 4000);
    } catch (err: any) {
      alert(`Failed to download report: ${err.message}`);
    } finally {
      setIsDownloadingPdf(false);
    }
  };

  if (!patient) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
        <div
          className="glass-card empty-state-card"
          style={{ padding: '64px 32px' }}
        >
          <div className="empty-state-icon" style={{ width: '64px', height: '64px' }}>
            <Users size={32} color="#38bdf8" />
          </div>
          <h2 className="empty-state-title" style={{ fontSize: '1.4rem' }}>No Patient Selected</h2>
          <p className="empty-state-desc">
            Please select an existing patient from the top navigation bar or initialize a new patient intake profile to view longitudinal trends, extracted lab results, and safety alerts.
          </p>
          <button
            onClick={() => onNavigate('patient-intake')}
            className="btn btn-primary"
            style={{ padding: '12px 24px', fontSize: '0.95rem' }}
          >
            <UserPlus size={18} />
            <span>Create New Patient</span>
          </button>
        </div>
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Top Banner / Welcome */}
      <div
        className="glass-card"
        style={{
          padding: '24px',
          background: 'linear-gradient(135deg, rgba(15, 23, 42, 0.9) 0%, rgba(30, 41, 59, 0.6) 100%)',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          borderLeft: '4px solid #0ea5e9',
        }}
      >
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
            <span className="pulse-dot" />
            <span style={{ fontSize: '0.75rem', fontWeight: 700, color: '#38bdf8', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              Active Clinical Workspace
            </span>
          </div>
          <h1 style={{ fontSize: '1.6rem', fontWeight: 800, color: 'var(--text-main)', letterSpacing: '-0.02em' }}>
            {patient.name}
          </h1>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginTop: '4px' }}>
            <span>
              Age: {patient.age || 'Unspecified'} • Sex: {patient.sex || 'Unspecified'} • Patient ID: {patient.identifier || `PAT-${String(patient.id).padStart(4, '0')}`} •{' '}
              <span style={{ color: '#38bdf8' }}>{reports.length} report{reports.length === 1 ? '' : 's'} on record</span>
            </span>
          </p>
        </div>

        <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap', alignItems: 'center' }}>
          <button
            onClick={() => onNavigate('patient-intake')}
            className="btn btn-secondary"
            style={{ borderColor: 'rgba(56, 189, 248, 0.4)', color: '#38bdf8' }}
            title="Create a new patient"
          >
            <UserPlus size={16} />
            <span>+ New Patient</span>
          </button>
          
          <button
            onClick={() => onNavigate('upload')}
            className="btn btn-secondary"
            title="Add a new diagnostic lab report"
          >
            <PlusCircle size={16} />
            <span>+ Add Report</span>
          </button>

          <button
            onClick={handleDownloadPdf}
            disabled={isDownloadingPdf}
            className="btn btn-primary"
            style={{
              background: pdfSuccess
                ? 'linear-gradient(135deg, #059669, #047857)'
                : 'linear-gradient(135deg, #0284c7, #0369a1)',
            }}
            title="Generate and download full clinical report PDF"
          >
            {pdfSuccess ? <Check size={16} /> : <Download size={16} />}
            <span>{isDownloadingPdf ? 'Generating PDF...' : pdfSuccess ? 'Downloaded' : 'Download PDF'}</span>
          </button>
        </div>
      </div>

      {/* Critical Alert Callout if Active Conflicts Exist */}
      {criticalConflicts.length > 0 && (
        <div
          style={{
            background: 'rgba(244, 63, 94, 0.1)',
            border: '1px solid rgba(244, 63, 94, 0.4)',
            borderRadius: 'var(--radius-lg)',
            padding: '16px 20px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            boxShadow: '0 0 20px rgba(244, 63, 94, 0.15)',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
            <div style={{ width: '40px', height: '40px', borderRadius: '10px', background: 'rgba(244, 63, 94, 0.2)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#f43f5e' }}>
              <AlertTriangle size={22} />
            </div>
            <div>
              <div style={{ fontWeight: 700, color: '#fda4af', fontSize: '0.95rem' }}>
                {criticalConflicts.length} Safety Conflict{criticalConflicts.length > 1 ? 's' : ''} Detected
              </div>
              <div style={{ fontSize: '0.8rem', color: '#cbd5e1' }}>
                {criticalConflicts[0].description}
              </div>
            </div>
          </div>

          <button onClick={() => onNavigate('conflicts')} className="btn btn-danger" style={{ fontSize: '0.8rem', padding: '6px 14px' }}>
            <span>Review Conflicts</span>
            <ArrowRight size={14} />
          </button>
        </div>
      )}

      {/* KPI Metrics Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '16px' }}>
        {/* Reports Metric */}
        <div className="glass-card" style={{ padding: '20px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <div>
              <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-dim)', textTransform: 'uppercase' }}>
                Diagnostic Reports
              </div>
              <div style={{ fontSize: '2rem', fontWeight: 800, color: 'var(--text-main)', marginTop: '4px', fontFamily: 'var(--font-mono)' }}>
                {reports.length}
              </div>
            </div>
            <div style={{ width: '38px', height: '38px', borderRadius: '8px', background: 'rgba(56, 189, 248, 0.12)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#38bdf8' }}>
              <FileText size={20} />
            </div>
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '8px' }}>
            Latest: {latestReport?.report_date ? new Date(latestReport.report_date).toLocaleDateString() : 'None'}
          </div>
        </div>

        {/* Safety Conflicts Metric */}
        <div className="glass-card" style={{ padding: '20px', borderLeft: activeConflicts.length > 0 ? '3px solid #f43f5e' : undefined }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <div>
              <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-dim)', textTransform: 'uppercase' }}>
                Active Conflicts
              </div>
              <div style={{ fontSize: '2rem', fontWeight: 800, color: activeConflicts.length > 0 ? '#f43f5e' : '#10b981', marginTop: '4px', fontFamily: 'var(--font-mono)' }}>
                {activeConflicts.length}
              </div>
            </div>
            <div style={{ width: '38px', height: '38px', borderRadius: '8px', background: activeConflicts.length > 0 ? 'rgba(244, 63, 94, 0.12)' : 'rgba(16, 185, 129, 0.12)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: activeConflicts.length > 0 ? '#f43f5e' : '#10b981' }}>
              <AlertTriangle size={20} />
            </div>
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '8px' }}>
            {activeConflicts.length > 0 ? `${criticalConflicts.length} high severity` : 'All safe & reconciled'}
          </div>
        </div>

        {/* Review Status Metric */}
        <div className="glass-card" style={{ padding: '20px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <div>
              <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-dim)', textTransform: 'uppercase' }}>
                Review Status
              </div>
              <div style={{ fontSize: '1.2rem', fontWeight: 700, color: '#f59e0b', marginTop: '8px' }}>
                {latestReport?.processing_status || 'READY'}
              </div>
            </div>
            <div style={{ width: '38px', height: '38px', borderRadius: '8px', background: 'rgba(245, 158, 11, 0.12)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#f59e0b' }}>
              <ClipboardCheck size={20} />
            </div>
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '12px' }}>
            Requires clinician authorization
          </div>
        </div>

        {/* Clarifications Metric */}
        <div className="glass-card" style={{ padding: '20px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <div>
              <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-dim)', textTransform: 'uppercase' }}>
                Clarifications
              </div>
              <div style={{ fontSize: '2rem', fontWeight: 800, color: 'var(--text-main)', marginTop: '4px', fontFamily: 'var(--font-mono)' }}>
                {pendingQuestions.length}
              </div>
            </div>
            <div style={{ width: '38px', height: '38px', borderRadius: '8px', background: 'rgba(168, 85, 247, 0.12)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#c084fc' }}>
              <HelpCircle size={20} />
            </div>
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '8px' }}>
            {pendingQuestions.length} pending provider answers
          </div>
        </div>
      </div>

      {/* Main Grid: Reports on Record & Quick Clinical Actions */}
      <div style={{ display: 'grid', gridTemplateColumns: 'minmax(0, 1fr) 340px', gap: '20px', alignItems: 'start' }}>
        {/* Reports Table Card */}
        <div className="glass-card" style={{ padding: '20px', minWidth: 0, overflow: 'hidden' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
            <div>
              <h2 style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--text-main)' }}>Reports on Record</h2>
              <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Chronological history of lab and diagnostic documents</p>
            </div>
            <button onClick={() => onNavigate('upload')} className="btn btn-secondary" style={{ fontSize: '0.75rem', padding: '5px 12px' }}>
              + Add Report
            </button>
          </div>

          {reports.length === 0 ? (
            <div className="empty-state-card" style={{ padding: '40px 20px' }}>
              <div className="empty-state-icon">
                <FileText size={28} />
              </div>
              <div className="empty-state-title">No Reports on Record</div>
              <div className="empty-state-desc">
                No diagnostic documents have been added for this patient. Add a report to extract lab parameters and generate clinical insights.
              </div>
              <button
                onClick={() => onNavigate('upload')}
                className="btn btn-primary"
                style={{ fontSize: '0.85rem' }}
              >
                <PlusCircle size={16} />
                <span>Add Medical Report</span>
              </button>
            </div>
          ) : (
            <div className="data-table-container" style={{ overflowX: 'auto', width: '100%' }}>
              <table className="data-table" style={{ width: '100%', minWidth: '540px' }}>
                <thead>
                  <tr>
                    <th>Date</th>
                    <th>Document</th>
                    <th>Source Lab</th>
                    <th>Parameters</th>
                    <th>Status</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {reports.map((r) => {
                    const statusBadgeClass =
                      r.processing_status === 'VALIDATED'
                        ? 'badge-normal'
                        : r.processing_status === 'REVIEW_REQUIRED'
                        ? 'badge-high'
                        : r.processing_status === 'FAILED'
                        ? 'badge-critical'
                        : 'badge-purple';

                    return (
                      <tr key={r.id}>
                        <td style={{ fontWeight: 600, whiteSpace: 'nowrap' }}>
                          {r.report_date ? new Date(r.report_date).toLocaleDateString() : 'N/A'}
                        </td>
                        <td>
                          <div
                            style={{ fontWeight: 600, color: 'var(--text-main)', maxWidth: '200px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}
                            title={r.original_filename || `Report #${r.id}`}
                          >
                            {r.original_filename || `Report #${r.id}`}
                          </div>
                          <div style={{ fontSize: '0.72rem', color: 'var(--text-dim)' }}>{r.report_type || 'Lab Panel'}</div>
                        </td>
                        <td style={{ color: 'var(--text-muted)', maxWidth: '140px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }} title={r.source_name || 'Standard Lab'}>
                          {r.source_name || 'Standard Lab'}
                        </td>
                        <td style={{ fontFamily: 'var(--font-mono)' }}>{r.lab_results?.length || 0}</td>
                        <td>
                          <span className={`badge ${statusBadgeClass}`}>
                            {r.processing_status}
                          </span>
                        </td>
                        <td>
                          <button
                            onClick={() => {
                              onSelectReport(r.id);
                              onNavigate('results');
                            }}
                            className="btn btn-secondary"
                            style={{ padding: '4px 10px', fontSize: '0.75rem', whiteSpace: 'nowrap' }}
                          >
                            <span>Inspect</span>
                            <ArrowRight size={12} />
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Clinical Quick Actions & Safety Summary */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', minWidth: '320px' }}>
          <div className="glass-card" style={{ padding: '20px' }}>
            <h2 style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--text-main)', marginBottom: '12px' }}>
              Quick Clinical Navigation
            </h2>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              <button
                onClick={() => onNavigate('results')}
                className="btn btn-secondary"
                style={{ justifyContent: 'space-between', padding: '12px 14px' }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <Activity size={16} color="#38bdf8" />
                  <span>Lab Results & Ranges</span>
                </div>
                <ArrowRight size={14} color="var(--text-dim)" />
              </button>

              <button
                onClick={() => onNavigate('conflicts')}
                className="btn btn-secondary"
                style={{ justifyContent: 'space-between', padding: '12px 14px' }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <AlertTriangle size={16} color="#f43f5e" />
                  <span>Safety Conflicts ({activeConflicts.length})</span>
                </div>
                <ArrowRight size={14} color="var(--text-dim)" />
              </button>

              <button
                onClick={() => onNavigate('comparison')}
                className="btn btn-secondary"
                style={{ justifyContent: 'space-between', padding: '12px 14px' }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <TrendingUp size={16} color="#10b981" />
                  <span>Longitudinal Comparisons</span>
                </div>
                <ArrowRight size={14} color="var(--text-dim)" />
              </button>

              <button
                onClick={() => onNavigate('insights')}
                className="btn btn-secondary"
                style={{ justifyContent: 'space-between', padding: '12px 14px' }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <BrainCircuit size={16} color="#c084fc" />
                  <span>Clinical Insights</span>
                </div>
                <ArrowRight size={14} color="var(--text-dim)" />
              </button>

              <button
                onClick={() => onNavigate('review')}
                className="btn btn-secondary"
                style={{ justifyContent: 'space-between', padding: '12px 14px' }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <ClipboardCheck size={16} color="#f59e0b" />
                  <span>Review & Sign-Off</span>
                </div>
                <ArrowRight size={14} color="var(--text-dim)" />
              </button>
            </div>
          </div>

          {/* Safety Notice */}
          <div className="safety-banner">
            <ShieldCheck size={24} style={{ flexShrink: 0, color: '#f59e0b' }} />
            <div>
              <strong>Safety Guardrail Active:</strong> AI extraction uses strict JSON schemas and deterministic normalization. Out-of-range statuses are computed mathematically.
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
