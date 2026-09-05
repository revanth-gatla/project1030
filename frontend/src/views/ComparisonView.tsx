import React, { useState } from 'react';
import {
  TrendingUp,
  TrendingDown,
  Minus,
  GitCompare,
  ArrowRight
} from 'lucide-react';
import { Report, Comparison } from '../types';
import { TabType } from '../components/Sidebar';

interface ComparisonViewProps {
  reports: Report[];
  comparison: Comparison | null;
  onSelectReports: (prevId: number, currId: number) => void;
  onNavigate?: (tab: TabType) => void;
}

export const ComparisonView: React.FC<ComparisonViewProps> = ({
  reports,
  comparison,
  onSelectReports,
  onNavigate,
}) => {
  const validReports = reports.filter(
    (r) => (r.lab_results && r.lab_results.length > 0) || r.processing_status === 'VALIDATED'
  );
  const sortedReports = [...validReports].sort((a, b) => {
    const dateA = a.report_date ? new Date(a.report_date).getTime() : 0;
    const dateB = b.report_date ? new Date(b.report_date).getTime() : 0;
    return dateA - dateB;
  });
  const displayReports = sortedReports.length > 0 ? sortedReports : reports;

  const [prevId, setPrevId] = useState<number>(() => {
    if (comparison?.previous_report_id) return comparison.previous_report_id;
    return displayReports.length > 1 ? displayReports[0].id : displayReports[0]?.id || 0;
  });

  const [currId, setCurrId] = useState<number>(() => {
    if (comparison?.current_report_id) return comparison.current_report_id;
    return displayReports.length > 1 ? displayReports[displayReports.length - 1].id : displayReports[0]?.id || 0;
  });

  const handleCompareClick = () => {
    if (prevId && currId && prevId !== currId) {
      onSelectReports(prevId, currId);
    }
  };

  const results = comparison?.results || [];

  if (displayReports.length < 2) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
        <div
          className="glass-card"
          style={{
            padding: '48px 32px',
            textAlign: 'center',
            background: 'linear-gradient(135deg, rgba(15, 23, 42, 0.9), rgba(30, 41, 59, 0.7))',
            border: '1px solid rgba(16, 185, 129, 0.25)',
            borderRadius: 'var(--radius-lg)',
          }}
        >
          <div
            style={{
              width: '64px',
              height: '64px',
              borderRadius: '16px',
              background: 'rgba(16, 185, 129, 0.12)',
              border: '1px solid rgba(16, 185, 129, 0.3)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              margin: '0 auto 20px auto',
              color: '#34d399',
            }}
          >
            <GitCompare size={32} />
          </div>

          <h2 style={{ fontSize: '1.3rem', fontWeight: 800, color: 'var(--text-main)', marginBottom: '8px' }}>
            Longitudinal Trajectory Requires 2+ Processed Reports
          </h2>

          <p style={{ fontSize: '0.88rem', color: 'var(--text-muted)', maxWidth: '580px', margin: '0 auto 24px auto', lineHeight: '1.5' }}>
            MedLens calculates paired biomarker trajectories across chronological lab reports. Currently, this patient has{' '}
            <strong style={{ color: 'var(--text-main)' }}>
              {displayReports.length === 0 ? 'no processed reports' : 'only 1 report'}
            </strong>{' '}
            with extracted laboratory parameters. Ingest an additional report (such as a follow-up or previous baseline) to activate automated delta shift calculations, direction tracking, and percentage variance detection.
          </p>

          {onNavigate && (
            <button
              onClick={() => onNavigate('upload')}
              className="btn btn-primary"
              style={{ padding: '10px 22px', fontSize: '0.9rem', margin: '0 auto' }}
            >
              <span>+ Add Follow-up Report</span>
              <ArrowRight size={16} />
            </button>
          )}
        </div>
      </div>
    );
  }

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
          borderLeft: '4px solid #10b981',
          flexWrap: 'wrap',
          gap: '16px',
        }}
      >
        <div>
          <h1 style={{ fontSize: '1.3rem', fontWeight: 800, color: 'var(--text-main)' }}>
            Longitudinal Lab Trajectory Comparison
          </h1>
          <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)', marginTop: '4px' }}>
            Automated paired-parameter delta tracking, direction classification, and percentage variance detection.
          </p>
        </div>

        {/* Report Pair Selectors */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
            <span style={{ fontSize: '0.7rem', color: 'var(--text-dim)', textTransform: 'uppercase' }}>Baseline Report:</span>
            <select
              value={prevId}
              onChange={(e) => setPrevId(Number(e.target.value))}
              className="form-select"
              style={{ width: '220px' }}
            >
              {displayReports.map((r) => (
                <option key={r.id} value={r.id}>
                  {r.report_date ? new Date(r.report_date).toLocaleDateString() : `Report #${r.id}`} - {r.source_name || r.original_filename || 'Lab'}
                </option>
              ))}
            </select>
          </div>

          <ArrowRight size={18} color="var(--text-dim)" style={{ marginTop: '16px' }} />

          <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
            <span style={{ fontSize: '0.7rem', color: 'var(--text-dim)', textTransform: 'uppercase' }}>Current Report:</span>
            <select
              value={currId}
              onChange={(e) => setCurrId(Number(e.target.value))}
              className="form-select"
              style={{ width: '220px' }}
            >
              {displayReports.map((r) => (
                <option key={r.id} value={r.id}>
                  {r.report_date ? new Date(r.report_date).toLocaleDateString() : `Report #${r.id}`} - {r.source_name || r.original_filename || 'Lab'}
                </option>
              ))}
            </select>
          </div>

          <button
            onClick={handleCompareClick}
            disabled={prevId === currId}
            className="btn btn-primary"
            style={{ marginTop: '16px', fontSize: '0.82rem', padding: '8px 16px' }}
          >
            <GitCompare size={15} />
            <span>Compute Shift</span>
          </button>
        </div>
      </div>

      {/* Trajectory Highlights Cards */}
      {results.length > 0 && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '16px' }}>
          {results.slice(0, 4).map((item) => {
            const dir = item.direction || item.change_direction || 'STABLE';
            const isIncrease = dir === 'INCREASED';
            const isDecrease = dir === 'DECREASED';
            const pct = item.percentage_change ?? item.change_percent;
            const delta = item.absolute_change ?? item.change_delta;
            const unit = item.unit || item.current_unit || item.previous_unit || '';

            return (
              <div key={item.id} className="glass-card" style={{ padding: '18px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                  <span style={{ fontSize: '0.8rem', fontWeight: 700, color: 'var(--text-main)' }}>
                    {item.canonical_name}
                  </span>
                  <span
                    className={`badge ${
                      isIncrease ? 'badge-high' : isDecrease ? 'badge-low' : 'badge-normal'
                    }`}
                  >
                    {pct !== null && pct !== undefined
                      ? `${pct > 0 ? '+' : ''}${pct.toFixed(1)}%`
                      : dir}
                  </span>
                </div>

                <div style={{ display: 'flex', alignItems: 'baseline', gap: '8px', marginTop: '10px' }}>
                  <span style={{ fontSize: '0.85rem', color: 'var(--text-dim)', fontFamily: 'var(--font-mono)' }}>
                    {item.previous_value || '—'}
                  </span>
                  <span style={{ color: 'var(--text-dim)' }}>→</span>
                  <span style={{ fontSize: '1.25rem', fontWeight: 800, color: 'var(--text-main)', fontFamily: 'var(--font-mono)' }}>
                    {item.current_value || '—'}
                  </span>
                  <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{unit}</span>
                </div>

                <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: '6px' }}>
                  Delta: {delta !== null && delta !== undefined ? (delta > 0 ? `+${delta}` : delta) : 'N/A'} {unit}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Main Longitudinal Comparison Table */}
      <div className="glass-card" style={{ padding: '0', overflow: 'hidden' }}>
        <div style={{ padding: '16px 20px', borderBottom: '1px solid var(--border-dim)' }}>
          <h2 style={{ fontSize: '0.95rem', fontWeight: 700, color: 'var(--text-main)' }}>
            Paired Parameter Variance Table
          </h2>
        </div>

        {results.length === 0 ? (
          <div style={{ padding: '40px', textAlign: 'center', color: 'var(--text-dim)' }}>
            <GitCompare size={36} style={{ opacity: 0.4, margin: '0 auto 12px auto' }} />
            <div>No longitudinal comparison computed yet between the selected reports.</div>
            <div style={{ fontSize: '0.78rem', marginTop: '6px' }}>
              Select a baseline report and current report above, then click "Compute Shift".
            </div>
          </div>
        ) : (
          <div className="data-table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Canonical Lab Parameter</th>
                  <th>Baseline Value</th>
                  <th>Current Value</th>
                  <th>Unit</th>
                  <th>Direction</th>
                  <th>Delta Shift</th>
                  <th>% Change</th>
                  <th>Clinical Status</th>
                </tr>
              </thead>
              <tbody>
                {results.map((r) => {
                  const dir = r.direction || r.change_direction || 'STABLE';
                  const delta = r.absolute_change ?? r.change_delta;
                  const pct = r.percentage_change ?? r.change_percent;
                  const unit = r.unit || r.current_unit || r.previous_unit || '—';
                  const isSig = r.is_significant || (pct !== null && pct !== undefined && Math.abs(pct) >= 15);

                  let badgeClass = 'badge-normal';
                  let icon = <Minus size={12} />;

                  if (dir === 'INCREASED') {
                    badgeClass = 'badge-high';
                    icon = <TrendingUp size={12} />;
                  } else if (dir === 'DECREASED') {
                    badgeClass = 'badge-low';
                    icon = <TrendingDown size={12} />;
                  }

                  return (
                    <tr key={r.id}>
                      <td style={{ fontWeight: 700, color: 'var(--text-main)' }}>
                        {r.canonical_name}
                      </td>

                      <td style={{ fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>
                        {r.previous_value || '—'}
                      </td>

                      <td style={{ fontFamily: 'var(--font-mono)', fontWeight: 800, color: 'var(--text-main)' }}>
                        {r.current_value || '—'}
                      </td>

                      <td style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>
                        {unit}
                      </td>

                      <td>
                        <span className={`badge ${badgeClass}`}>
                          {icon}
                          <span>{dir}</span>
                        </span>
                      </td>

                      <td style={{ fontFamily: 'var(--font-mono)' }}>
                        {delta !== null && delta !== undefined
                          ? delta > 0
                            ? `+${delta}`
                            : delta
                          : '—'}
                      </td>

                      <td style={{ fontFamily: 'var(--font-mono)', fontWeight: 700 }}>
                        {pct !== null && pct !== undefined
                          ? `${pct > 0 ? '+' : ''}${pct.toFixed(1)}%`
                          : '—'}
                      </td>

                      <td>
                        {isSig ? (
                          <span className="badge badge-critical" style={{ fontSize: '0.68rem' }}>
                            Significant Shift
                          </span>
                        ) : (
                          <span className="badge badge-normal" style={{ fontSize: '0.68rem' }}>
                            Expected Variance
                          </span>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
