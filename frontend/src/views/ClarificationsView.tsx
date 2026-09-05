import React, { useState } from 'react';
import {
  HelpCircle,
  CheckCircle2,
  Send
} from 'lucide-react';
import { ClarificationQuestion } from '../types';

interface ClarificationsViewProps {
  questions: ClarificationQuestion[];
  onAnswerQuestion: (id: number, answer: string) => Promise<void>;
}

export const ClarificationsView: React.FC<ClarificationsViewProps> = ({
  questions,
  onAnswerQuestion,
}) => {
  const [answers, setAnswers] = useState<Record<number, string>>({});
  const [answeringId, setAnsweringId] = useState<number | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const pendingQuestions = questions.filter((q) => !q.answered);
  const answeredQuestions = questions.filter((q) => q.answered);

  const handleAnswer = async (id: number) => {
    const text = answers[id];
    if (!text || !text.trim()) return;

    try {
      setIsSubmitting(true);
      await onAnswerQuestion(id, text.trim());
      setAnsweringId(null);
    } finally {
      setIsSubmitting(false);
    }
  };

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
          borderLeft: '4px solid #38bdf8',
        }}
      >
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <h1 style={{ fontSize: '1.3rem', fontWeight: 800, color: 'var(--text-main)' }}>
              Clinical Clarification Questions
            </h1>
            <span className="badge badge-purple">
              {pendingQuestions.length} Pending Clinician Review
            </span>
          </div>
          <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)', marginTop: '4px' }}>
            AI-flagged clinical ambiguities, missing pre-test variables, and medication adherence questions.
          </p>
        </div>
      </div>

      {/* Pending Questions */}
      <div>
        <h2 style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--text-main)', marginBottom: '14px' }}>
          Questions Requiring Clinician Input ({pendingQuestions.length})
        </h2>

        {pendingQuestions.length === 0 ? (
          <div className="glass-card" style={{ padding: '36px', textAlign: 'center', color: '#86efac' }}>
            <CheckCircle2 size={36} style={{ margin: '0 auto 10px auto' }} />
            <div style={{ fontWeight: 700 }}>All Clarification Inquiries Answered</div>
            <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginTop: '4px' }}>
              No outstanding ambiguities flagged for this patient.
            </div>
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            {pendingQuestions.map((q) => (
              <div key={q.id} className="glass-card" style={{ padding: '20px', borderLeft: '3px solid #38bdf8' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '8px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flex: 1 }}>
                    <HelpCircle size={18} color="#38bdf8" style={{ flexShrink: 0, marginTop: '2px' }} />
                    <span style={{ fontSize: '0.92rem', fontWeight: 700, color: 'var(--text-main)' }}>
                      {q.question}
                    </span>
                  </div>
                  <div style={{ display: 'flex', gap: '6px', flexShrink: 0 }}>
                    {q.category && <span className="badge badge-purple">{q.category}</span>}
                    {q.priority !== undefined && q.priority >= 1 && (
                      <span className={`badge ${q.priority === 1 ? 'badge-critical' : q.priority === 2 ? 'badge-high' : 'badge-normal'}`}>
                        P{q.priority}
                      </span>
                    )}
                  </div>
                </div>

                {/* Clinical Rationale */}
                {q.reason && (
                  <div style={{
                    background: 'rgba(56, 189, 248, 0.06)',
                    border: '1px solid rgba(56, 189, 248, 0.15)',
                    borderRadius: 'var(--radius-sm, 6px)',
                    padding: '10px 14px',
                    marginBottom: '12px',
                    marginLeft: '26px',
                  }}>
                    <div style={{ fontSize: '0.7rem', fontWeight: 700, color: '#94a3b8', textTransform: 'uppercase', marginBottom: '3px' }}>
                      Clinical Rationale
                    </div>
                    <div style={{ fontSize: '0.82rem', color: '#bae6fd', lineHeight: '1.5' }}>
                      {q.reason}
                    </div>
                  </div>
                )}

                <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', marginTop: '14px' }}>
                  <textarea
                    value={answers[q.id] || ''}
                    onChange={(e) => setAnswers({ ...answers, [q.id]: e.target.value })}
                    className="form-textarea"
                    rows={2}
                    placeholder="Enter clinician response / clinical findings..."
                  />

                  <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
                    <button
                      onClick={() => { setAnsweringId(q.id); handleAnswer(q.id); }}
                      disabled={isSubmitting || !answers[q.id]?.trim()}
                      className="btn btn-primary"
                      style={{ fontSize: '0.8rem', padding: '6px 14px' }}
                    >
                      <Send size={14} />
                      <span>{isSubmitting && answeringId === q.id ? 'Submitting...' : 'Record Answer'}</span>
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Answered Questions Archive */}
      {answeredQuestions.length > 0 && (
        <div style={{ marginTop: '12px' }}>
          <h2 style={{ fontSize: '0.95rem', fontWeight: 700, color: 'var(--text-dim)', marginBottom: '12px' }}>
            Resolved Inquiries ({answeredQuestions.length})
          </h2>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {answeredQuestions.map((aq) => (
              <div
                key={aq.id}
                className="glass-card"
                style={{
                  padding: '16px',
                  background: 'rgba(15, 23, 42, 0.4)',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '6px',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--text-muted)', fontSize: '0.85rem' }}>
                  <CheckCircle2 size={16} color="#10b981" />
                  <span style={{ fontWeight: 600 }}>{aq.question}</span>
                </div>
                <div style={{ fontSize: '0.82rem', color: '#bae6fd', marginLeft: '24px', background: 'rgba(56, 189, 248, 0.08)', padding: '8px 12px', borderRadius: 'var(--radius-sm)', border: '1px solid rgba(56, 189, 248, 0.2)' }}>
                  <strong>Clinician Response:</strong> {aq.answer || 'Confirmed during consultation.'}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
