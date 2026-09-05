import React, { useState } from 'react';
import {
  AlertTriangle,
  CheckCircle2,
  ShieldCheck
} from 'lucide-react';
import { Conflict } from '../types';

interface ConflictsViewProps {
  conflicts: Conflict[];
  onResolveConflict: (id: number, notes?: string) => Promise<void>;
}

export const ConflictsView: React.FC<ConflictsViewProps> = ({
  conflicts,
  onResolveConflict,
}) => {
  const [resolvingId, setResolvingId] = useState<number | null>(null);
  const [resolutionNotes, setResolutionNotes] = useState<Record<number, string>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);

  const uniqueConflicts = React.useMemo(() => {
    const seen = new Set<string>();
    return conflicts.filter((c) => {
      const key = `${c.conflict_type}|${c.description}|${c.status}`;
      if (seen.has(key)) return false;
      seen.add(key);
      return true;
    });
  }, [conflicts]);

  const activeConflicts = uniqueConflicts.filter((c) => c.status === 'OPEN' || c.status === 'ACKNOWLEDGED');
  const resolvedConflicts = uniqueConflicts.filter((c) => c.status === 'RESOLVED' || c.status === 'DISMISSED');

  const handleResolve = async (conflictId: number) => {
    try {
      setIsSubmitting(true);
      const note = resolutionNotes[conflictId] || 'Acknowledged and addressed by attending clinician.';
      await onResolveConflict(conflictId, note);
      setResolvingId(null);
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
          borderLeft: activeConflicts.length > 0 ? '4px solid #f43f5e' : '4px solid #10b981',
        }}
      >
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <h1 style={{ fontSize: '1.3rem', fontWeight: 800, color: 'var(--text-main)' }}>
              Clinical Safety Conflicts & Contradictions
            </h1>
            {activeConflicts.length > 0 ? (
              <span className="badge badge-critical">{activeConflicts.length} Active Safety Alerts</span>
            ) : (
              <span className="badge badge-normal">All Safety Checks Clear</span>
            )}
          </div>
          <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)', marginTop: '4px' }}>
            Automated cross-referencing between patient intake allergies, current medications, and report recommendations.
          </p>
        </div>
      </div>

      {/* Active Conflicts List */}
      <div>
        <h2 style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--text-main)', marginBottom: '14px' }}>
          Active Safety Contradictions ({activeConflicts.length})
        </h2>

        {activeConflicts.length === 0 ? (
          <div className="glass-card" style={{ padding: '36px', textAlign: 'center', color: '#86efac' }}>
            <ShieldCheck size={40} style={{ margin: '0 auto 12px auto', opacity: 0.9 }} />
            <div style={{ fontSize: '1.05rem', fontWeight: 700 }}>Zero Active Clinical Conflicts</div>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '4px' }}>
              All documented allergies, medications, and laboratory values are clinically reconciled.
            </div>
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            {activeConflicts.map((c) => {
              const isCritical = c.severity === 'CRITICAL' || c.severity === 'HIGH';
              const cardBorder = isCritical ? 'rgba(244, 63, 94, 0.4)' : 'rgba(245, 158, 11, 0.4)';
              const cardBg = isCritical ? 'rgba(244, 63, 94, 0.06)' : 'rgba(245, 158, 11, 0.05)';

              return (
                <div
                  key={c.id}
                  className="glass-card"
                  style={{
                    padding: '22px',
                    border: `1px solid ${cardBorder}`,
                    background: cardBg,
                    boxShadow: isCritical ? '0 0 24px rgba(244, 63, 94, 0.12)' : undefined,
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '12px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                      <div
                        style={{
                          width: '36px',
                          height: '36px',
                          borderRadius: '8px',
                          background: isCritical ? 'rgba(244, 63, 94, 0.2)' : 'rgba(245, 158, 11, 0.2)',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          color: isCritical ? '#f43f5e' : '#f59e0b',
                        }}
                      >
                        <AlertTriangle size={20} />
                      </div>
                      <div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                          <span className={`badge ${isCritical ? 'badge-critical' : 'badge-high'}`}>
                            {c.severity} SEVERITY
                          </span>
                          <span className="badge badge-purple">{c.conflict_type}</span>
                        </div>
                      </div>
                    </div>

                    <div style={{ fontSize: '0.72rem', color: 'var(--text-dim)' }}>
                      Detected: {new Date(c.created_at).toLocaleDateString()}
                    </div>
                  </div>

                  {/* Description */}
                  <div style={{ fontSize: '0.92rem', fontWeight: 600, color: '#f8fafc', lineHeight: '1.5', marginBottom: '16px' }}>
                    {c.description}
                  </div>

                  {/* Discrepancy Sources */}
                  {(c.source_a || c.source_b) && (
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '16px' }}>
                      {c.source_a && (
                        <div style={{ background: 'rgba(15, 23, 42, 0.7)', padding: '12px', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-dim)' }}>
                          <div style={{ fontSize: '0.7rem', fontWeight: 700, color: '#94a3b8', textTransform: 'uppercase', marginBottom: '4px' }}>
                            Source Fact A (Patient Record)
                          </div>
                          <div style={{ fontSize: '0.82rem', color: '#e2e8f0', fontFamily: 'var(--font-mono)' }}>
                            {c.source_a}
                          </div>
                        </div>
                      )}
                      {c.source_b && (
                        <div style={{ background: 'rgba(15, 23, 42, 0.7)', padding: '12px', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-dim)' }}>
                          <div style={{ fontSize: '0.7rem', fontWeight: 700, color: '#94a3b8', textTransform: 'uppercase', marginBottom: '4px' }}>
                            Source Fact B (Report Recommendation / Lab Shift)
                          </div>
                          <div style={{ fontSize: '0.82rem', color: '#e2e8f0', fontFamily: 'var(--font-mono)' }}>
                            {c.source_b}
                          </div>
                        </div>
                      )}
                    </div>
                  )}

                  {/* Resolution Action */}
                  {resolvingId === c.id ? (
                    <div style={{ background: 'rgba(15, 23, 42, 0.8)', padding: '16px', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)', display: 'flex', flexDirection: 'column', gap: '10px' }}>
                      <label style={{ fontSize: '0.78rem', fontWeight: 600, color: 'var(--text-muted)' }}>
                        Clinician Resolution Justification & Plan
                      </label>
                      <textarea
                        value={resolutionNotes[c.id] || ''}
                        onChange={(e) => setResolutionNotes({ ...resolutionNotes, [c.id]: e.target.value })}
                        className="form-textarea"
                        rows={2}
                        placeholder="e.g. Consulted cardiologist; ACE-inhibitor recommendation cancelled due to angioedema allergy. Alternative ARB/calcium blocker prescribed."
                      />
                      <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px' }}>
                        <button onClick={() => setResolvingId(null)} className="btn btn-secondary" style={{ fontSize: '0.78rem', padding: '6px 12px' }}>
                          Cancel
                        </button>
                        <button
                          onClick={() => handleResolve(c.id)}
                          disabled={isSubmitting}
                          className="btn btn-primary"
                          style={{ fontSize: '0.78rem', padding: '6px 14px' }}
                        >
                          <CheckCircle2 size={14} />
                          <span>{isSubmitting ? 'Resolving...' : 'Confirm Resolution'}</span>
                        </button>
                      </div>
                    </div>
                  ) : (
                    <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
                      <button
                        onClick={() => setResolvingId(c.id)}
                        className="btn btn-primary"
                        style={{ fontSize: '0.8rem', padding: '6px 14px' }}
                      >
                        <CheckCircle2 size={15} />
                        <span>Resolve Conflict</span>
                      </button>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Resolved Conflicts History */}
      {resolvedConflicts.length > 0 && (
        <div style={{ marginTop: '12px' }}>
          <h2 style={{ fontSize: '0.95rem', fontWeight: 700, color: 'var(--text-dim)', marginBottom: '12px' }}>
            Resolved Conflicts Archive ({resolvedConflicts.length})
          </h2>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {resolvedConflicts.map((rc) => (
              <div
                key={rc.id}
                className="glass-card"
                style={{
                  padding: '14px 18px',
                  background: 'rgba(15, 23, 42, 0.4)',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  opacity: 0.75,
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <CheckCircle2 size={16} color="#10b981" />
                  <div>
                    <div style={{ fontSize: '0.85rem', color: 'var(--text-main)', textDecoration: 'line-through' }}>
                      {rc.description}
                    </div>
                    {rc.resolution_notes && (
                      <div style={{ fontSize: '0.75rem', color: '#86efac', marginTop: '2px' }}>
                        Note: {rc.resolution_notes}
                      </div>
                    )}
                  </div>
                </div>
                <span className="badge badge-normal">Resolved</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
