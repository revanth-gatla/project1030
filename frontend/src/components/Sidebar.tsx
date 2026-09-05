import React from 'react';
import {
  LayoutDashboard,
  UserPlus,
  UserCheck,
  FileUp,
  Table,
  ShieldAlert,
  GitCompare,
  BrainCircuit,
  HelpCircle,
  ClipboardCheck,
  ChevronRight
} from 'lucide-react';

export type TabType =
  | 'overview'
  | 'patient-intake'
  | 'upload'
  | 'intake'
  | 'results'
  | 'conflicts'
  | 'comparison'
  | 'insights'
  | 'clarifications'
  | 'review';

interface SidebarProps {
  currentTab: TabType;
  onTabChange: (tab: TabType) => void;
  conflictCount: number;
  questionCount: number;
  reviewRequired: boolean;
}

export const Sidebar: React.FC<SidebarProps> = ({
  currentTab,
  onTabChange,
  conflictCount,
  questionCount,
  reviewRequired,
}) => {
  const navItems = [
    { id: 'overview' as TabType, label: 'Overview', icon: LayoutDashboard },
    { id: 'patient-intake' as TabType, label: 'New Patient', icon: UserPlus },
    { id: 'upload' as TabType, label: 'Add Report', icon: FileUp },
    { id: 'intake' as TabType, label: 'Patient Record', icon: UserCheck },
    { id: 'results' as TabType, label: 'Lab Results', icon: Table },
    {
      id: 'conflicts' as TabType,
      label: 'Conflicts',
      icon: ShieldAlert,
      badge: conflictCount > 0 ? conflictCount : undefined,
      badgeColor: 'var(--status-critical-bg)',
      badgeText: '#fda4af',
    },
    { id: 'comparison' as TabType, label: 'Comparisons', icon: GitCompare },
    { id: 'insights' as TabType, label: 'Insights', icon: BrainCircuit },
    {
      id: 'clarifications' as TabType,
      label: 'Clarifications',
      icon: HelpCircle,
      badge: questionCount > 0 ? questionCount : undefined,
      badgeColor: 'rgba(56, 189, 248, 0.15)',
      badgeText: '#7dd3fc',
    },
    {
      id: 'review' as TabType,
      label: 'Review',
      icon: ClipboardCheck,
      badge: reviewRequired ? 'Action' : undefined,
      badgeColor: 'rgba(245, 158, 11, 0.15)',
      badgeText: '#fde68a',
    },
  ];

  return (
    <aside className="sidebar">
      <div style={{ padding: '20px 16px 12px 16px' }}>
        <div style={{ fontSize: '0.72rem', fontWeight: 700, color: 'var(--text-dim)', textTransform: 'uppercase', letterSpacing: '0.08em', paddingLeft: '8px' }}>
          Clinical Intelligence
        </div>
      </div>

      <nav style={{ display: 'flex', flexDirection: 'column', gap: '4px', padding: '0 12px', flex: 1 }}>
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = currentTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => onTabChange(item.id)}
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: '10px 14px',
                borderRadius: 'var(--radius-md)',
                background: isActive ? 'rgba(14, 165, 233, 0.15)' : 'transparent',
                color: isActive ? '#38bdf8' : 'var(--text-muted)',
                border: isActive ? '1px solid rgba(56, 189, 248, 0.3)' : '1px solid transparent',
                cursor: 'pointer',
                transition: 'all 0.18s ease',
                textAlign: 'left',
                width: '100%',
                fontWeight: isActive ? 600 : 500,
                fontSize: '0.86rem',
              }}
              onMouseEnter={(e) => {
                if (!isActive) {
                  e.currentTarget.style.background = 'rgba(255, 255, 255, 0.04)';
                  e.currentTarget.style.color = 'var(--text-main)';
                }
              }}
              onMouseLeave={(e) => {
                if (!isActive) {
                  e.currentTarget.style.background = 'transparent';
                  e.currentTarget.style.color = 'var(--text-muted)';
                }
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                <Icon size={18} color={isActive ? '#38bdf8' : 'var(--text-dim)'} />
                <span>{item.label}</span>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                {item.badge !== undefined && (
                  <span
                    style={{
                      background: item.badgeColor,
                      color: item.badgeText,
                      padding: '2px 7px',
                      borderRadius: '10px',
                      fontSize: '0.7rem',
                      fontWeight: 700,
                    }}
                  >
                    {item.badge}
                  </span>
                )}
                {isActive && <ChevronRight size={14} color="#38bdf8" />}
              </div>
            </button>
          );
        })}
      </nav>

      {/* Safety Compliance Footnote */}
      <div style={{ padding: '16px', borderTop: '1px solid var(--border-dim)' }}>
        <div style={{
          background: 'rgba(245, 158, 11, 0.06)',
          border: '1px solid rgba(245, 158, 11, 0.2)',
          borderRadius: 'var(--radius-sm)',
          padding: '10px',
          fontSize: '0.72rem',
          color: '#fde68a'
        }}>
          <div style={{ fontWeight: 700, marginBottom: '2px' }}>Clinical Decision Support</div>
          <div style={{ color: 'var(--text-muted)', fontSize: '0.68rem', lineHeight: '1.3' }}>
            All findings require provider verification. Deterministic ranges & audit trails enabled.
          </div>
        </div>
      </div>
    </aside>
  );
};
