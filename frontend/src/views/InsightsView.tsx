import React, { useState } from 'react';
import {
  BrainCircuit,
  Sparkles,
  ShieldCheck,
  CheckCircle2,
  FileCheck
} from 'lucide-react';
import { Report, Insight } from '../types';

interface InsightsViewProps {
  report: Report | null;
  insight: Insight | null;
  onGenerateInsights: (reportId: number) => Promise<void>;
}

export const InsightsView: React.FC<InsightsViewProps> = ({
  report,
  insight,
  onGenerateInsights,
}) => {
  const [isGenerating, setIsGenerating] = useState(false);

  if (!report) {
    return (
      <div className="glass-card" style={{ padding: '40px', textAlign: 'center' }}>
        <p style={{ color: 'var(--text-dim)' }}>Select a report to view AI Clinical Intelligence Insights.</p>
      </div>
    );
  }

  const handleGenerate = async () => {
    try {
      setIsGenerating(true);
      await onGenerateInsights(report.id);
    } finally {
      setIsGenerating(false);
    }
  };

  const keyFindingsList =
    Array.isArray(insight?.key_findings)
      ? insight.key_findings
      : typeof insight?.key_findings === 'string'
      ? insight.key_findings.split('\n').filter(Boolean)
      : [];

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
          borderLeft: '4px solid #a855f7',
          flexWrap: 'wrap',
          gap: '16px',
        }}
      >
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <h1 style={{ fontSize: '1.3rem', fontWeight: 800, color: 'var(--text-main)' }}>
              AI Clinical Intelligence & Plain-English Insights
            </h1>
          </div>
          <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)', marginTop: '4px' }}>
            Multi-modal synthesis of extracted lab parameters, reference variances, and safety contraindications.
          </p>
        </div>

        <button
          onClick={handleGenerate}
          disabled={isGenerating}
          className="btn btn-primary"
          style={{ background: 'linear-gradient(135deg, #7c3aed, #6366f1)' }}
        >
          <Sparkles size={16} />
          <span>{isGenerating ? 'Synthesizing...' : 'Regenerate Insights'}</span>
        </button>
      </div>

      {/* Mandatory Safety Notice */}
      <div className="safety-banner">
        <ShieldCheck size={26} style={{ flexShrink: 0, color: '#f59e0b' }} />
        <div>
          <strong>Medical Safety Disclaimer:</strong> MedLens is an automated clinical decision support tool designed to assist healthcare professionals in extracting, normalizing, and comparing medical reports. MedLens does not formulate autonomous diagnoses or prescribe therapies. All insights and findings must be evaluated and authorized by a licensed clinician.
        </div>
      </div>

      {!insight ? (
        <div className="glass-card" style={{ padding: '40px', textAlign: 'center' }}>
          <BrainCircuit size={40} color="#a855f7" style={{ opacity: 0.5, margin: '0 auto 12px auto' }} />
          <div style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--text-main)', marginBottom: '16px' }}>
            No Clinical Intelligence Summary Generated Yet
          </div>
          <button onClick={handleGenerate} disabled={isGenerating} className="btn btn-primary">
            <Sparkles size={15} />
            <span>{isGenerating ? 'Generating...' : 'Generate Clinical Summary'}</span>
          </button>
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: '3fr 2fr', gap: '20px' }}>
          {/* Main Structured Synthesis */}
          <div className="glass-card" style={{ padding: '24px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
              <BrainCircuit size={18} color="#c084fc" />
              <h2 style={{ fontSize: '1.05rem', fontWeight: 700, color: 'var(--text-main)' }}>
                Plain-English Clinical Synthesis
              </h2>
            </div>

            <div
              style={{
                background: 'rgba(15, 23, 42, 0.6)',
                border: '1px solid var(--border-dim)',
                borderRadius: 'var(--radius-md)',
                padding: '18px',
                color: '#e2e8f0',
                fontSize: '0.88rem',
                lineHeight: '1.7',
                whiteSpace: 'pre-wrap',
                fontFamily: 'var(--font-sans)',
              }}
            >
              {insight.summary}
            </div>
          </div>

          {/* Key Findings Bulleted Checklist */}
          <div className="glass-card" style={{ padding: '24px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
              <FileCheck size={18} color="#38bdf8" />
              <h2 style={{ fontSize: '1.05rem', fontWeight: 700, color: 'var(--text-main)' }}>
                Key Findings Checklist
              </h2>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              {keyFindingsList.length > 0 ? (
                keyFindingsList.map((kf, i) => (
                  <div
                    key={i}
                    style={{
                      display: 'flex',
                      alignItems: 'flex-start',
                      gap: '10px',
                      background: 'rgba(56, 189, 248, 0.05)',
                      border: '1px solid rgba(56, 189, 248, 0.18)',
                      borderRadius: 'var(--radius-md)',
                      padding: '12px',
                    }}
                  >
                    <CheckCircle2 size={16} color="#38bdf8" style={{ marginTop: '2px', flexShrink: 0 }} />
                    <span style={{ fontSize: '0.84rem', color: '#f1f5f9', lineHeight: '1.4' }}>
                      {kf.replace(/^[-•*]\s*/, '')}
                    </span>
                  </div>
                ))
              ) : (
                <div style={{ color: 'var(--text-dim)', fontSize: '0.85rem' }}>
                  No individual key findings extracted.
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
