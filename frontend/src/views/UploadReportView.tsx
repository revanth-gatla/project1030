import React, { useState } from 'react';
import {
  UploadCloud,
  FileCode,
  CheckCircle2,
  AlertCircle,
  Loader2,
  Calendar,
  Building,
  ArrowRight,
  User,
  Table,
  BrainCircuit,
  ShieldAlert,
  GitCompare,
  UserCheck,
  UserPlus
} from 'lucide-react';
import { Report, Patient } from '../types';
import { TabType } from '../components/Sidebar';

interface UploadReportViewProps {
  patient: Patient | null;
  onUploadFile: (file: File, reportDate?: string, sourceName?: string) => Promise<Report>;
  onPasteText: (data: { text: string; report_date?: string; source_name?: string }) => Promise<Report>;
  onProcessReport: (reportId: number) => Promise<Report>;
  onProcessingComplete: (report: Report) => void;
  onNavigate?: (tab: TabType) => void;
  onStartNewIntake?: () => void;
}

export const UploadReportView: React.FC<UploadReportViewProps> = ({
  patient,
  onUploadFile,
  onPasteText,
  onProcessReport,
  onProcessingComplete,
  onNavigate,
  onStartNewIntake,
}) => {
  const [activeMode, setActiveMode] = useState<'upload' | 'paste'>('upload');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [pastedText, setPastedText] = useState('');
  const [reportDate, setReportDate] = useState('');
  const [sourceName, setSourceName] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [currentStep, setCurrentStep] = useState<number>(0);
  const [error, setError] = useState<string | null>(null);
  const [completedReport, setCompletedReport] = useState<Report | null>(null);

  const pipelineSteps = [
    'Document Validation & Sanitization',
    'Document Text Extraction',
    'Entity & Metric Extraction',
    'Deterministic Parameter Normalization',
    'Mathematical Reference Range Classification',
    'Safety Conflict & Drug Allergy Detection',
    'Longitudinal Shift Calculation',
  ];

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      setSelectedFile(e.dataTransfer.files[0]);
    }
  };

  const handleExecute = async () => {
    if (!patient) {
      setError('Please select or create a patient first before adding medical reports.');
      return;
    }

    setError(null);
    setIsProcessing(true);
    setCurrentStep(1);
    setCompletedReport(null);

    try {
      let createdReport: Report;

      if (activeMode === 'upload') {
        if (!selectedFile) {
          throw new Error('Please select a file to upload.');
        }
        setCurrentStep(2);
        createdReport = await onUploadFile(selectedFile, reportDate || undefined, sourceName || undefined);
      } else {
        if (!pastedText.trim()) {
          throw new Error('Please enter or paste report text.');
        }
        setCurrentStep(2);
        createdReport = await onPasteText({
          text: pastedText,
          report_date: reportDate,
          source_name: sourceName || 'Clinical Diagnostics',
        });
      }

      // Kick off processing in parallel with step animations
      const processPromise = onProcessReport(createdReport.id);

      // Animate progress smoothly through steps
      for (let s = 3; s <= pipelineSteps.length; s++) {
        await new Promise((r) => setTimeout(r, 260));
        setCurrentStep(s);
      }

      const processed = await processPromise;
      setCurrentStep(pipelineSteps.length + 1);
      setCompletedReport(processed);
      onProcessingComplete(processed);
    } catch (err: any) {
      setError(err.message || 'Processing failed.');
      setCurrentStep(0);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleResetForAnother = () => {
    setSelectedFile(null);
    setPastedText('');
    setCompletedReport(null);
    setCurrentStep(0);
    setError(null);
  };

  return (
    <div style={{ maxWidth: '950px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Header & Context */}
      <div
        className="glass-card"
        style={{
          padding: '20px 24px',
          background: 'linear-gradient(135deg, rgba(99, 102, 241, 0.12), rgba(14, 165, 233, 0.08))',
          borderLeft: '4px solid #6366f1',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '16px',
        }}
      >
        <div>
          <h1 style={{ fontSize: '1.35rem', fontWeight: 800, color: 'var(--text-main)', margin: 0 }}>
            Add Medical Report
          </h1>
          <p style={{ fontSize: '0.84rem', color: 'var(--text-muted)', marginTop: '4px' }}>
            Upload standard pathology/lab documents (PDF, DOCX, TXT) or paste raw clinical printouts.
            MedLens performs parameter extraction, canonical normalization, deterministic reference ranges, and safety conflict detection.
          </p>
        </div>

        {patient && (
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '12px',
              background: 'rgba(15, 23, 42, 0.7)',
              padding: '8px 16px',
              borderRadius: 'var(--radius-md)',
              border: '1px solid var(--border-subtle)',
            }}
          >
            <div
              style={{
                width: '36px',
                height: '36px',
                borderRadius: '10px',
                background: 'rgba(56, 189, 248, 0.18)',
                color: '#38bdf8',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <User size={18} />
            </div>
            <div>
              <div style={{ fontSize: '0.86rem', fontWeight: 700, color: 'var(--text-main)' }}>
                {patient.name}
              </div>
              <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                {patient.identifier || `ID: ${patient.id}`} • {patient.age || 'N/A'} yo • {patient.sex}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* No Patient Warning Alert */}
      {!patient && (
        <div
          style={{
            background: 'rgba(245, 158, 11, 0.12)',
            border: '1px solid rgba(245, 158, 11, 0.35)',
            padding: '16px 20px',
            borderRadius: 'var(--radius-md)',
            color: '#fde68a',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            flexWrap: 'wrap',
            gap: '12px',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <AlertCircle size={22} color="#f59e0b" />
            <div>
              <div style={{ fontWeight: 700, fontSize: '0.9rem' }}>Patient Profile Required</div>
              <div style={{ fontSize: '0.78rem', color: '#fef3c7', marginTop: '2px' }}>
                Each medical report must be associated with a patient profile. Please create a new patient profile or select an existing patient.
              </div>
            </div>
          </div>
          {onStartNewIntake && (
            <button
              onClick={onStartNewIntake}
              className="btn btn-primary"
              style={{ fontSize: '0.82rem', padding: '8px 16px', background: '#f59e0b', color: '#0f172a' }}
            >
              <UserPlus size={15} />
              <span>+ New Patient</span>
            </button>
          )}
        </div>
      )}

      {error && (
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
          }}
        >
          <AlertCircle size={18} />
          <span>{error}</span>
        </div>
      )}

      {/* Post-Processing Clinician Action Center */}
      {completedReport && (
        <div
          className="glass-card"
          style={{
            padding: '24px',
            background: 'linear-gradient(135deg, rgba(16, 185, 129, 0.15), rgba(15, 23, 42, 0.95))',
            border: '1px solid rgba(16, 185, 129, 0.4)',
            borderRadius: 'var(--radius-lg)',
            display: 'flex',
            flexDirection: 'column',
            gap: '18px',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '12px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <div
                style={{
                  width: '42px',
                  height: '42px',
                  borderRadius: '10px',
                  background: 'rgba(16, 185, 129, 0.25)',
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
                  Report Successfully Processed & Classified
                </h3>
                <div style={{ fontSize: '0.82rem', color: 'var(--text-muted)', marginTop: '3px' }}>
                  Extracted <strong>{completedReport.lab_results?.length || 0} lab biomarkers</strong> with deterministic reference ranges and safety audit trail.
                </div>
              </div>
            </div>

            <button
              onClick={handleResetForAnother}
              className="btn btn-secondary"
              style={{ fontSize: '0.82rem', padding: '6px 14px' }}
            >
              + Add Another Report
            </button>
          </div>

          <div style={{ borderTop: '1px solid rgba(255, 255, 255, 0.08)', paddingTop: '16px' }}>
            <div style={{ fontSize: '0.76rem', color: 'var(--text-dim)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: '10px', fontWeight: 700 }}>
              Clinical Navigation:
            </div>
            <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
              {onNavigate && (
                <>
                  <button
                    onClick={() => onNavigate('results')}
                    className="btn btn-primary"
                    style={{ fontSize: '0.86rem', padding: '9px 16px' }}
                  >
                    <Table size={16} />
                    <span>Review Extraction</span>
                  </button>

                  <button
                    onClick={() => onNavigate('insights')}
                    className="btn btn-secondary"
                    style={{ fontSize: '0.86rem', padding: '9px 16px' }}
                  >
                    <BrainCircuit size={16} color="#38bdf8" />
                    <span>Clinical Insights</span>
                  </button>

                  <button
                    onClick={() => onNavigate('conflicts')}
                    className="btn btn-secondary"
                    style={{ fontSize: '0.86rem', padding: '9px 16px' }}
                  >
                    <ShieldAlert size={16} color="#f43f5e" />
                    <span>Safety Conflicts</span>
                  </button>

                  <button
                    onClick={() => onNavigate('comparison')}
                    className="btn btn-secondary"
                    style={{ fontSize: '0.86rem', padding: '9px 16px' }}
                  >
                    <GitCompare size={16} color="#10b981" />
                    <span>Compare Reports</span>
                  </button>

                  <button
                    onClick={() => onNavigate('intake')}
                    className="btn btn-secondary"
                    style={{ fontSize: '0.86rem', padding: '9px 16px' }}
                  >
                    <UserCheck size={16} color="#818cf8" />
                    <span>Patient Record</span>
                  </button>
                </>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Mode Switcher */}
      <div
        style={{
          display: 'flex',
          gap: '8px',
          background: 'rgba(15, 23, 42, 0.6)',
          padding: '4px',
          borderRadius: 'var(--radius-md)',
          width: 'fit-content',
          border: '1px solid var(--border-dim)',
        }}
      >
        <button
          onClick={() => setActiveMode('upload')}
          disabled={isProcessing}
          style={{
            padding: '8px 18px',
            borderRadius: 'var(--radius-sm)',
            border: 'none',
            background: activeMode === 'upload' ? 'rgba(56, 189, 248, 0.18)' : 'transparent',
            color: activeMode === 'upload' ? '#38bdf8' : 'var(--text-muted)',
            fontWeight: activeMode === 'upload' ? 600 : 500,
            fontSize: '0.85rem',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
          }}
        >
          <UploadCloud size={16} />
          <span>File Upload (PDF/DOCX/TXT)</span>
        </button>

        <button
          onClick={() => setActiveMode('paste')}
          disabled={isProcessing}
          style={{
            padding: '8px 18px',
            borderRadius: 'var(--radius-sm)',
            border: 'none',
            background: activeMode === 'paste' ? 'rgba(56, 189, 248, 0.18)' : 'transparent',
            color: activeMode === 'paste' ? '#38bdf8' : 'var(--text-muted)',
            fontWeight: activeMode === 'paste' ? 600 : 500,
            fontSize: '0.85rem',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
          }}
        >
          <FileCode size={16} />
          <span>Direct Text Paste</span>
        </button>
      </div>

      {/* Upload or Paste Form Container */}
      <div className="glass-card" style={{ padding: '28px' }}>
        {activeMode === 'upload' ? (
          <div
            onDragOver={handleDragOver}
            onDrop={handleDrop}
            style={{
              border: selectedFile ? '2px solid #38bdf8' : '2px dashed var(--border-subtle)',
              borderRadius: 'var(--radius-lg)',
              padding: '44px 20px',
              textAlign: 'center',
              background: selectedFile ? 'rgba(56, 189, 248, 0.05)' : 'rgba(255, 255, 255, 0.01)',
              cursor: 'pointer',
              transition: 'all 0.2s ease',
            }}
            onClick={() => document.getElementById('report-file-input')?.click()}
          >
            <input
              id="report-file-input"
              type="file"
              accept=".pdf,.docx,.txt"
              style={{ display: 'none' }}
              onChange={(e) => {
                if (e.target.files && e.target.files[0]) {
                  setSelectedFile(e.target.files[0]);
                }
              }}
            />

            <div
              style={{
                width: '56px',
                height: '56px',
                borderRadius: '50%',
                background: 'rgba(56, 189, 248, 0.15)',
                color: '#38bdf8',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                margin: '0 auto 16px auto',
              }}
            >
              <UploadCloud size={28} />
            </div>

            {selectedFile ? (
              <div>
                <div style={{ fontWeight: 700, color: 'var(--text-main)', fontSize: '1rem' }}>
                  {selectedFile.name}
                </div>
                <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginTop: '4px' }}>
                  {(selectedFile.size / 1024).toFixed(1)} KB • Click or drop another file to replace
                </div>
              </div>
            ) : (
              <div>
                <div style={{ fontWeight: 600, color: 'var(--text-main)', fontSize: '0.95rem' }}>
                  Drag & Drop Medical Report Document Here
                </div>
                <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '4px' }}>
                  Supports PDF, Word (.docx), or plain text (.txt) lab exports
                </div>
                <button
                  type="button"
                  className="btn btn-secondary"
                  style={{ marginTop: '16px', fontSize: '0.82rem', padding: '6px 16px' }}
                >
                  Browse Local Files
                </button>
              </div>
            )}
          </div>
        ) : (
          <div>
            <div style={{ marginBottom: '8px' }}>
              <label style={{ fontSize: '0.82rem', fontWeight: 600, color: 'var(--text-muted)' }}>
                Paste Raw Clinical Text / Lab Printout
              </label>
            </div>

            <textarea
              value={pastedText}
              onChange={(e) => setPastedText(e.target.value)}
              className="form-textarea"
              rows={9}
              placeholder="Paste raw medical report text or lab results here..."
              style={{ fontFamily: 'var(--font-mono)', fontSize: '0.82rem' }}
            />
          </div>
        )}

        {/* Metadata row */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginTop: '20px' }}>
          <div>
            <label
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                fontSize: '0.78rem',
                color: 'var(--text-muted)',
                marginBottom: '6px',
                fontWeight: 600,
              }}
            >
              <Calendar size={14} /> Report Date (Optional — auto-detected from report)
            </label>
            <input
              type="date"
              value={reportDate}
              onChange={(e) => setReportDate(e.target.value)}
              className="form-input"
            />
          </div>

          <div>
            <label
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                fontSize: '0.78rem',
                color: 'var(--text-muted)',
                marginBottom: '6px',
                fontWeight: 600,
              }}
            >
              <Building size={14} /> Diagnostic Source / Lab Facility
            </label>
            <input
              type="text"
              value={sourceName}
              onChange={(e) => setSourceName(e.target.value)}
              className="form-input"
              placeholder="e.g. Metro Diagnostics, Quest, LabCorp"
            />
          </div>
        </div>

        {/* Execute Button */}
        <div style={{ marginTop: '24px', display: 'flex', justifyContent: 'flex-end' }}>
          <button
            onClick={handleExecute}
            disabled={isProcessing || !patient}
            className="btn btn-primary"
            style={{ padding: '10px 24px', fontSize: '0.9rem' }}
          >
            {isProcessing ? (
              <>
                <Loader2 size={16} className="spin" />
                <span>Running Extraction Pipeline...</span>
              </>
            ) : (
              <>
                <span>Extract & Analyze Report</span>
                <ArrowRight size={16} />
              </>
            )}
          </button>
        </div>
      </div>

      {/* Live Pipeline Visualizer */}
      {isProcessing && (
        <div className="glass-card" style={{ padding: '24px', borderLeft: '4px solid #38bdf8' }}>
          <h3 style={{ fontSize: '0.95rem', fontWeight: 700, color: 'var(--text-main)', marginBottom: '16px' }}>
            MedLens Extraction & Analysis Pipeline
          </h3>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {pipelineSteps.map((stepName, idx) => {
              const stepNum = idx + 1;
              const isDone = currentStep > stepNum;
              const isCurrent = currentStep === stepNum;

              return (
                <div
                  key={stepName}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '12px',
                    padding: '8px 12px',
                    borderRadius: 'var(--radius-sm)',
                    background: isCurrent ? 'rgba(56, 189, 248, 0.12)' : 'transparent',
                    color: isDone ? '#10b981' : isCurrent ? '#38bdf8' : 'var(--text-dim)',
                    transition: 'all 0.2s ease',
                  }}
                >
                  <div style={{ width: '20px', display: 'flex', justifyContent: 'center' }}>
                    {isDone ? (
                      <CheckCircle2 size={18} color="#10b981" />
                    ) : isCurrent ? (
                      <Loader2 size={18} className="spin" color="#38bdf8" />
                    ) : (
                      <div
                        style={{
                          width: '8px',
                          height: '8px',
                          borderRadius: '50%',
                          background: 'rgba(255, 255, 255, 0.15)',
                        }}
                      />
                    )}
                  </div>
                  <span style={{ fontSize: '0.85rem', fontWeight: isCurrent ? 600 : 400 }}>
                    {stepName}
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};
