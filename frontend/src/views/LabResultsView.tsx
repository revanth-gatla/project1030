import React, { useState } from 'react';
import {
  Search,
  Eye,
  Edit2,
  CheckCircle2,
  TrendingDown,
  TrendingUp,
  ShieldCheck,
  AlertTriangle
} from 'lucide-react';
import { Report, LabResult } from '../types';

interface LabResultsViewProps {
  reports: Report[];
  selectedReportId: number | null;
  onSelectReportId: (id: number) => void;
  onOpenProvenance: (result: LabResult) => void;
  onOpenEdit: (result: LabResult) => void;
  onVerifyResult: (id: number) => void;
}

export const LabResultsView: React.FC<LabResultsViewProps> = ({
  reports,
  selectedReportId,
  onSelectReportId,
  onOpenProvenance,
  onOpenEdit,
  onVerifyResult,
}) => {
  const currentReport = reports.find((r) => r.id === selectedReportId) || reports[0];
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<'ALL' | 'OUT_OF_RANGE' | 'WITHIN'>('ALL');

  if (!currentReport) {
    return (
      <div className="glass-card" style={{ padding: '40px', textAlign: 'center' }}>
        <p style={{ color: 'var(--text-dim)' }}>No reports available for this patient. Please upload or paste a report.</p>
      </div>
    );
  }

  const results = currentReport.lab_results || [];

  const filteredResults = results.filter((item) => {
    const matchesSearch =
      item.canonical_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      item.original_name.toLowerCase().includes(searchTerm.toLowerCase());

    if (!matchesSearch) return false;

    if (statusFilter === 'OUT_OF_RANGE') {
      return (
        item.reference_status === 'ABOVE' ||
        item.reference_status === 'HIGH' ||
        item.reference_status === 'BELOW' ||
        item.reference_status === 'LOW'
      );
    }
    if (statusFilter === 'WITHIN') {
      return item.reference_status === 'WITHIN' || item.reference_status === 'NORMAL';
    }
    return true;
  });

  const outOfRangeCount = results.filter(
    (r) =>
      r.reference_status === 'ABOVE' ||
      r.reference_status === 'HIGH' ||
      r.reference_status === 'BELOW' ||
      r.reference_status === 'LOW'
  ).length;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Header with Report Selector */}
      <div
        className="glass-card"
        style={{
          padding: '20px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '16px',
        }}
      >
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <h1 style={{ fontSize: '1.3rem', fontWeight: 800, color: 'var(--text-main)' }}>
              Structured Lab Results
            </h1>
            <span className="badge badge-purple" style={{ textTransform: 'uppercase' }}>
              {currentReport.processing_status}
            </span>
          </div>
          <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)', marginTop: '4px' }}>
            Extracted parameters with deterministic range classification and audit trail provenance.
          </p>
        </div>

        {/* Report Selector Dropdown */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <label style={{ fontSize: '0.82rem', color: 'var(--text-muted)', fontWeight: 600 }}>Select Report:</label>
          <select
            className="input-field"
            value={currentReport.id}
            onChange={(e) => onSelectReportId(Number(e.target.value))}
            style={{ width: '260px', padding: '8px 12px', fontSize: '0.85rem' }}
          >
            {reports.map((r) => (
              <option key={r.id} value={r.id}>
                {r.original_filename || `Report #${r.id}`} ({r.report_date ? new Date(r.report_date).toLocaleDateString() : 'No date'})
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Metrics Bar & Filters */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '12px',
        }}
      >
        <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
          <button
            onClick={() => setStatusFilter('ALL')}
            className={`btn ${statusFilter === 'ALL' ? 'btn-primary' : 'btn-secondary'}`}
            style={{ padding: '6px 14px', fontSize: '0.8rem' }}
          >
            All Results ({results.length})
          </button>
          <button
            onClick={() => setStatusFilter('OUT_OF_RANGE')}
            className={`btn ${statusFilter === 'OUT_OF_RANGE' ? 'btn-danger' : 'btn-secondary'}`}
            style={{ padding: '6px 14px', fontSize: '0.8rem' }}
          >
            <AlertTriangle size={13} />
            <span>Out of Range ({outOfRangeCount})</span>
          </button>
          <button
            onClick={() => setStatusFilter('WITHIN')}
            className={`btn ${statusFilter === 'WITHIN' ? 'btn-primary' : 'btn-secondary'}`}
            style={{ padding: '6px 14px', fontSize: '0.8rem' }}
          >
            Normal ({results.length - outOfRangeCount})
          </button>
        </div>

        <div style={{ position: 'relative', width: '280px' }}>
          <Search
            size={15}
            style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-dim)' }}
          />
          <input
            type="text"
            placeholder="Search parameter..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="input-field"
            style={{ paddingLeft: '36px', fontSize: '0.85rem' }}
          />
        </div>
      </div>

      {/* Results Table */}
      <div className="glass-card" style={{ padding: '0', overflow: 'hidden' }}>
        <div style={{ overflowX: 'auto' }}>
          <table className="data-table">
            <thead>
              <tr>
                <th>Test Parameter</th>
                <th>Observed Value</th>
                <th>Reference Range</th>
                <th>Distribution</th>
                <th>Status</th>
                <th>Confidence</th>
                <th style={{ textAlign: 'right' }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filteredResults.length === 0 ? (
                <tr>
                  <td colSpan={7} style={{ textAlign: 'center', padding: '40px', color: 'var(--text-dim)' }}>
                    No lab results found matching your criteria.
                  </td>
                </tr>
              ) : (
                filteredResults.map((item) => {
                  const isHigh = item.reference_status === 'ABOVE' || item.reference_status === 'HIGH';
                  const isLow = item.reference_status === 'BELOW' || item.reference_status === 'LOW';
                  const isWithin = item.reference_status === 'WITHIN' || item.reference_status === 'NORMAL';

                  let badgeClass = 'badge-normal';
                  let statusIcon = null;
                  let displayStatus = item.reference_status || 'UNKNOWN';

                  if (isHigh) {
                    badgeClass = 'badge-high';
                    statusIcon = <TrendingUp size={12} />;
                    displayStatus = 'HIGH';
                  } else if (isLow) {
                    badgeClass = 'badge-low';
                    statusIcon = <TrendingDown size={12} />;
                    displayStatus = 'LOW';
                  } else if (isWithin) {
                    displayStatus = 'WITHIN';
                  }

                  // Mathematical bar indicator calculation
                  let indicatorPercent = 50;
                  if (item.reference_low !== null && item.reference_low !== undefined &&
                      item.reference_high !== null && item.reference_high !== undefined &&
                      item.value_numeric !== null && item.value_numeric !== undefined) {
                    const low = item.reference_low;
                    const high = item.reference_high;
                    const span = high - low || 1;
                    const val = item.value_numeric;
                    // map low..high to 25%..75%
                    const calculated = 25 + ((val - low) / span) * 50;
                    indicatorPercent = Math.max(5, Math.min(95, calculated));
                  }

                  return (
                    <tr key={item.id}>
                      {/* Name & Canonical Name */}
                      <td>
                        <div style={{ fontWeight: 700, color: 'var(--text-main)' }}>{item.canonical_name}</div>
                        <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>Alias: {item.original_name}</div>
                      </td>

                      {/* Value & Unit */}
                      <td>
                        <span
                          style={{
                            fontFamily: 'var(--font-mono)',
                            fontSize: '0.95rem',
                            fontWeight: 800,
                            color: isHigh ? '#f59e0b' : isLow ? '#38bdf8' : 'var(--text-main)',
                          }}
                        >
                          {item.observed_value}
                        </span>{' '}
                        <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>{item.unit || ''}</span>
                      </td>

                      {/* Reference Range */}
                      <td style={{ color: 'var(--text-muted)', fontSize: '0.82rem', fontFamily: 'var(--font-mono)' }}>
                        {item.reference_range_text || '—'}
                      </td>

                      {/* Visual Range Bar */}
                      <td>
                        <div className="range-bar-wrapper">
                          <div className="range-bar-track">
                            <div
                              className="range-bar-normal-zone"
                              style={{ left: '25%', width: '50%' }}
                              title="Normal Reference Range Zone"
                            />
                            <div
                              className="range-bar-indicator"
                              style={{
                                left: `${indicatorPercent}%`,
                                background: isHigh ? '#f59e0b' : isLow ? '#0ea5e9' : '#10b981',
                              }}
                            />
                          </div>
                        </div>
                      </td>

                      {/* Status Badge */}
                      <td>
                        <span className={`badge ${badgeClass}`}>
                          {statusIcon}
                          <span>{displayStatus}</span>
                        </span>
                      </td>

                      {/* Confidence */}
                      <td>
                        {item.confidence !== null && item.confidence !== undefined ? (
                          <div style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '0.8rem', color: '#10b981', fontFamily: 'var(--font-mono)' }}>
                            <ShieldCheck size={14} />
                            <span>{Math.round(item.confidence * 100)}%</span>
                          </div>
                        ) : (
                          <span style={{ fontSize: '0.8rem', color: 'var(--text-dim)', fontFamily: 'var(--font-mono)' }}>
                            N/A
                          </span>
                        )}
                      </td>

                      {/* Actions: Traceability & Edit */}
                      <td style={{ textAlign: 'right' }}>
                        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '6px' }}>
                          <button
                            onClick={() => onOpenProvenance(item)}
                            className="btn btn-secondary"
                            style={{ padding: '4px 8px', fontSize: '0.75rem' }}
                            title="Inspect Source Text & Provenance"
                          >
                            <Eye size={13} color="#38bdf8" />
                            <span>Source</span>
                          </button>
                          <button
                            onClick={() => onOpenEdit(item)}
                            className="btn btn-secondary"
                            style={{ padding: '4px 8px', fontSize: '0.75rem' }}
                            title="Edit Result & Add Audit Note"
                          >
                            <Edit2 size={13} />
                          </button>
                          <button
                            onClick={() => onVerifyResult(item.id)}
                            className={`btn ${item.verified ? 'btn-secondary' : 'btn-primary'}`}
                            style={{ padding: '4px 8px', fontSize: '0.75rem' }}
                            title={item.verified ? 'Verified' : 'Click to Verify'}
                          >
                            <CheckCircle2 size={13} color={item.verified ? '#10b981' : '#ffffff'} />
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
