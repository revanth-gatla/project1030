import React from 'react';
import { Activity, User as UserIcon, LogOut, UserPlus } from 'lucide-react';
import { Patient, User } from '../types';

interface NavbarProps {
  user: User | null;
  patients: Patient[];
  selectedPatient: Patient | null;
  onSelectPatient: (p: Patient) => void;
  onNewIntake: () => void;
  onLogout: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({
  user,
  patients,
  selectedPatient,
  onSelectPatient,
  onNewIntake,
  onLogout,
}) => {
  return (
    <header className="top-navbar">
      <div style={{ display: 'flex', alignItems: 'center', gap: '24px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div style={{
            width: '36px',
            height: '36px',
            borderRadius: '10px',
            background: 'linear-gradient(135deg, #0ea5e9, #6366f1)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 0 16px rgba(14, 165, 233, 0.4)'
          }}>
            <Activity size={20} color="#ffffff" />
          </div>
          <div>
            <div style={{ fontFamily: 'var(--font-display)', fontWeight: 800, fontSize: '1.2rem', letterSpacing: '-0.02em', background: 'linear-gradient(to right, #f8fafc, #94a3b8)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
              MedLens
            </div>
            <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.08em', marginTop: '-2px' }}>
              Clinical Intelligence
            </div>
          </div>
        </div>

        {/* Patient Selector */}
        {patients.length > 0 && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', background: 'rgba(15, 23, 42, 0.8)', padding: '4px 10px', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)', fontWeight: 600, textTransform: 'uppercase' }}>Patient:</span>
            <select
              value={selectedPatient?.id || ''}
              onChange={(e) => {
                const p = patients.find(x => x.id === Number(e.target.value));
                if (p) onSelectPatient(p);
              }}
              style={{
                background: 'transparent',
                border: 'none',
                color: 'var(--text-main)',
                fontSize: '0.85rem',
                fontWeight: 600,
                cursor: 'pointer',
                outline: 'none',
              }}
            >
              {patients.map(p => (
                <option key={p.id} value={p.id} style={{ background: '#0f172a', color: '#f8fafc' }}>
                  {p.name} ({p.identifier || `ID: ${p.id}`})
                </option>
              ))}
            </select>
          </div>
        )}
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
        {/* Quick New Patient Button */}
        <button
          onClick={onNewIntake}
          className="btn btn-secondary"
          style={{ fontSize: '0.8rem', padding: '6px 14px', background: 'rgba(14, 165, 233, 0.12)', borderColor: 'rgba(56, 189, 248, 0.3)', color: '#38bdf8' }}
          title="Add a new patient"
        >
          <UserPlus size={15} />
          <span>+ New Patient</span>
        </button>

        {/* Clinician Profile */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', paddingLeft: '10px', borderLeft: '1px solid var(--border-dim)' }}>
          <div style={{
            width: '32px',
            height: '32px',
            borderRadius: '50%',
            background: 'rgba(56, 189, 248, 0.15)',
            border: '1px solid rgba(56, 189, 248, 0.3)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#38bdf8'
          }}>
            <UserIcon size={16} />
          </div>
          <div style={{ display: 'flex', flexDirection: 'column' }}>
            <span style={{ fontSize: '0.82rem', fontWeight: 600, color: 'var(--text-main)' }}>
              {user?.full_name || user?.email?.split('@')[0] || 'Clinician'}
            </span>
            <span style={{ fontSize: '0.68rem', color: 'var(--text-dim)' }}>
              {user?.role || 'Clinician Reviewer'}
            </span>
          </div>
          <button
            onClick={onLogout}
            style={{
              background: 'transparent',
              border: 'none',
              color: 'var(--text-dim)',
              cursor: 'pointer',
              padding: '6px',
              borderRadius: '6px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              marginLeft: '4px'
            }}
            title="Log out"
          >
            <LogOut size={16} />
          </button>
        </div>
      </div>
    </header>
  );
};
