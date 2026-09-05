import React, { useState, useEffect, useCallback } from 'react';
import { api } from './api/client';
import {
  User,
  Patient,
  Report,
  LabResult,
  Conflict,
  ClarificationQuestion,
  Comparison,
  Insight,
  Provenance,
  ReviewHistoryItem,
  PatientIntake,
  PatientCreate,
} from './types';
import { Navbar } from './components/Navbar';
import { Sidebar, TabType } from './components/Sidebar';
import { ProvenanceModal } from './components/ProvenanceModal';
import { EditLabResultModal } from './components/EditLabResultModal';
import { DashboardView } from './views/DashboardView';
import { PatientIntakeView } from './views/PatientIntakeView';
import { PatientWorkspaceView } from './views/PatientWorkspaceView';
import { UploadReportView } from './views/UploadReportView';
import { LabResultsView } from './views/LabResultsView';
import { ConflictsView } from './views/ConflictsView';
import { ComparisonView } from './views/ComparisonView';
import { InsightsView } from './views/InsightsView';
import { ClarificationsView } from './views/ClarificationsView';
import { ReviewCenterView } from './views/ReviewCenterView';
import { LoginView } from './views/LoginView';

export const App: React.FC = () => {
  // Auth state
  const [user, setUser] = useState<User | null>(null);
  const [isInitializing, setIsInitializing] = useState(true);

  // Core Clinical State
  const [patients, setPatients] = useState<Patient[]>([]);
  const [selectedPatient, setSelectedPatient] = useState<Patient | null>(null);
  const [reports, setReports] = useState<Report[]>([]);
  const [selectedReportId, setSelectedReportId] = useState<number | null>(null);
  const [conflicts, setConflicts] = useState<Conflict[]>([]);
  const [questions, setQuestions] = useState<ClarificationQuestion[]>([]);
  const [comparison, setComparison] = useState<Comparison | null>(null);
  const [currentInsight, setCurrentInsight] = useState<Insight | null>(null);
  const [reviewHistory, setReviewHistory] = useState<ReviewHistoryItem[]>([]);

  // UI Modals & Navigation
  const [currentTab, setCurrentTab] = useState<TabType>('overview');
  const [provenanceModalResult, setProvenanceModalResult] = useState<LabResult | null>(null);
  const [provenanceData, setProvenanceData] = useState<Provenance | null>(null);
  const [editModalResult, setEditModalResult] = useState<LabResult | null>(null);

  // Load Patient Data
  const loadPatientData = useCallback(async (patientId: number) => {
    try {
      const [p, rpts, confs, qs, revs] = await Promise.all([
        api.getPatient(patientId),
        api.getPatientReports(patientId).catch(() => []),
        api.getConflicts(patientId).catch(() => []),
        api.getQuestions(patientId).catch(() => []),
        api.getReviewHistory(patientId).catch(() => []),
      ]);

      const allReports = (p.reports && p.reports.length > 0) ? p.reports : (rpts || []);
      p.reports = allReports;

      setSelectedPatient(p);
      setReports(allReports);
      setConflicts(confs);
      setQuestions(qs);
      setReviewHistory(revs);

      const latest = allReports[0];
      if (latest) {
        setSelectedReportId(prev => (prev && allReports.some(r => r.id === prev) ? prev : latest.id));
        // Load insights if present
        try {
          const provs = await api.getProvenance(latest.id);
          if (provs && provs.length > 0) {
            setProvenanceData(provs[0]);
          }
        } catch {
          // ignore
        }
      }

      // If at least two reports with lab results exist, load comparison
      const reportsWithLabs = allReports.filter(
        (r) => (r.lab_results && r.lab_results.length > 0) || r.processing_status === 'VALIDATED'
      );
      if (reportsWithLabs.length >= 2) {
        try {
          const sorted = [...reportsWithLabs].sort((a, b) => {
            const dateA = a.report_date ? new Date(a.report_date).getTime() : 0;
            const dateB = b.report_date ? new Date(b.report_date).getTime() : 0;
            return dateA - dateB;
          });
          const baseline = sorted[0];
          const current = sorted[sorted.length - 1];
          const prevId = baseline.id;
          const currId = current.id;
          if (prevId !== currId) {
            const comp = await api.getComparison(patientId, prevId, currId);
            setComparison(comp);
          }
        } catch {
          // ignore
        }
      }
    } catch (err) {
      console.error('Failed to load patient data:', err);
    }
  }, []);

  // Initial Auth Check
  useEffect(() => {
    const checkAuth = async () => {
      const token = api.getToken();
      if (!token) {
        setIsInitializing(false);
        return;
      }
      try {
        const me = await api.getMe();
        setUser(me);
        const pts = await api.getPatients();
        setPatients(pts);
        if (pts.length > 0) {
          await loadPatientData(pts[0].id);
        }
      } catch (err) {
        console.warn('Session expired:', err);
        api.setToken(null);
        setUser(null);
      } finally {
        setIsInitializing(false);
      }
    };
    checkAuth();
  }, [loadPatientData]);

  // Auth Handlers
  const handleLogin = async (email: string, pass: string) => {
    const res = await api.login(email, pass);
    const me = res.user || (await api.getMe());
    setUser(me);
    const pts = await api.getPatients();
    setPatients(pts);
    if (pts.length > 0) {
      await loadPatientData(pts[0].id);
    }
  };

  const handleRegister = async (email: string, pass: string) => {
    const res = await api.register(email, pass);
    const me = res.user || (await api.getMe());
    setUser(me);
    const pts = await api.getPatients();
    setPatients(pts);
    if (pts.length > 0) {
      await loadPatientData(pts[0].id);
    }
  };

  const handleLogout = () => {
    api.setToken(null);
    setUser(null);
    setSelectedPatient(null);
    setReports([]);
    setConflicts([]);
    setQuestions([]);
    setComparison(null);
  };


  // Patient Select
  const handleSelectPatient = async (p: Patient) => {
    setSelectedPatient(p);
    await loadPatientData(p.id);
  };

  // Intake Update
  const handleUpdateIntake = async (intake: PatientIntake) => {
    if (!selectedPatient) return;
    const updated = await api.updateIntake(selectedPatient.id, intake);
    setSelectedPatient({ ...selectedPatient, intake: updated });
  };

  // Patient Intake Save
  const handleSavePatientIntake = async (data: PatientCreate): Promise<Patient> => {
    const created = await api.createPatient(data);
    setPatients((prev) => [created, ...prev.filter((p) => p.id !== created.id)]);
    setSelectedPatient(created);
    await loadPatientData(created.id);
    return created;
  };

  // Report Upload / Processing
  const handleUploadFile = async (file: File, reportDate?: string, sourceName?: string) => {
    if (!selectedPatient) throw new Error('No patient selected.');
    const rep = await api.uploadReport(selectedPatient.id, file, reportDate, sourceName);
    return rep;
  };

  const handlePasteText = async (data: { text: string; report_date?: string; source_name?: string }) => {
    if (!selectedPatient) throw new Error('No patient selected.');
    const rep = await api.pasteReport(selectedPatient.id, data);
    return rep;
  };

  const handleProcessReport = async (reportId: number) => {
    const processed = await api.processReport(reportId);
    return processed;
  };

  const handleProcessingComplete = async (rep: Report) => {
    setSelectedReportId(rep.id);
    setReports((prev) => {
      const idx = prev.findIndex((r) => r.id === rep.id);
      if (idx >= 0) {
        const updated = [...prev];
        updated[idx] = rep;
        return updated;
      }
      return [rep, ...prev];
    });
    if (selectedPatient) {
      await loadPatientData(selectedPatient.id);
    }
    setSelectedReportId(rep.id);
  };

  // Lab Results & Verification
  const handleVerifyResult = async (id: number) => {
    try {
      await api.updateLabResult(id, { verified: true });
      if (selectedPatient) {
        await loadPatientData(selectedPatient.id);
      }
    } catch (err) {
      console.error('Verify failed:', err);
    }
  };

  const handleSaveLabResult = async (id: number, update: Partial<LabResult>) => {
    await api.updateLabResult(id, update);
    if (selectedPatient) {
      await loadPatientData(selectedPatient.id);
    }
  };

  const handleOpenProvenance = async (res: LabResult) => {
    setProvenanceModalResult(res);
    try {
      const provs = await api.getProvenance(res.report_id);
      const matched = provs.find((p) => p.target_id === res.id) || provs[0];
      setProvenanceData(matched || null);
    } catch {
      setProvenanceData(null);
    }
  };

  // Conflicts
  const handleResolveConflict = async (id: number, notes?: string) => {
    await api.resolveConflict(id, notes);
    if (selectedPatient) {
      const confs = await api.getConflicts(selectedPatient.id);
      setConflicts(confs);
    }
  };

  // Clarification Qs
  const handleAnswerQuestion = async (id: number, answer: string) => {
    await api.answerQuestion(id, answer);
    if (selectedPatient) {
      const qs = await api.getQuestions(selectedPatient.id);
      setQuestions(qs);
    }
  };

  // Comparison
  const handleSelectReportsForComparison = async (prev: number, curr: number) => {
    if (!selectedPatient) return;
    try {
      const comp = await api.getComparison(selectedPatient.id, prev, curr);
      setComparison(comp);
    } catch (err) {
      console.error('Comparison error:', err);
    }
  };

  // Insights
  const handleGenerateInsights = async (repId: number) => {
    const ins = await api.generateInsights(repId);
    setCurrentInsight(ins);
    if (selectedPatient) {
      await loadPatientData(selectedPatient.id);
    }
  };

  // Review
  const handleSubmitReview = async (repId: number, data: { status: string; notes?: string }) => {
    await api.submitReview(repId, data);
    if (selectedPatient) {
      await loadPatientData(selectedPatient.id);
    }
  };

  if (isInitializing) {
    return (
      <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'var(--bg-app)', color: 'var(--text-muted)' }}>
        <div style={{ textAlign: 'center' }}>
          <div className="pulse-dot" style={{ margin: '0 auto 16px auto', width: '12px', height: '12px' }} />
          <div style={{ fontWeight: 600, fontSize: '0.9rem' }}>Initializing MedLens Platform...</div>
        </div>
      </div>
    );
  }

  if (!user) {
    return (
      <LoginView
        onLogin={handleLogin}
        onRegister={handleRegister}
      />
    );
  }

  const activeConflictCount = conflicts.filter((c) => c.status === 'OPEN' || c.status === 'ACKNOWLEDGED').length;
  const pendingQuestionCount = questions.filter((q) => !q.answered).length;
  const currentReport = reports.find((r) => r.id === selectedReportId) || reports[0] || null;
  const reviewRequired = currentReport?.processing_status === 'REVIEW_REQUIRED';

  return (
    <div className="app-container">
      {/* Left Sidebar Navigation */}
      <Sidebar
        currentTab={currentTab}
        onTabChange={setCurrentTab}
        conflictCount={activeConflictCount}
        questionCount={pendingQuestionCount}
        reviewRequired={reviewRequired}
      />

      <div className="main-content">
        {/* Top Navbar */}
        <Navbar
          user={user}
          patients={patients}
          selectedPatient={selectedPatient}
          onSelectPatient={handleSelectPatient}
          onNewIntake={() => setCurrentTab('patient-intake')}
          onLogout={handleLogout}
        />

        {/* View Routing */}
        <main className="content-body">
          {currentTab === 'overview' && (
            <DashboardView
              patient={selectedPatient}
              reports={reports}
              conflicts={conflicts}
              questions={questions}
              onNavigate={setCurrentTab}
              onSelectReport={setSelectedReportId}
            />
          )}

          {currentTab === 'patient-intake' && (
            <PatientIntakeView
              onSavePatient={handleSavePatientIntake}
              onProceedToUpload={(p) => {
                setSelectedPatient(p);
                setCurrentTab('upload');
              }}
              onOpenWorkspace={(p) => {
                setSelectedPatient(p);
                setCurrentTab('intake');
              }}
            />
          )}

          {currentTab === 'intake' && (
            <PatientWorkspaceView
              patient={selectedPatient}
              reports={reports}
              conflicts={conflicts}
              onUpdateIntake={handleUpdateIntake}
              onNavigate={setCurrentTab}
              onSelectReport={setSelectedReportId}
              onNewIntake={() => setCurrentTab('patient-intake')}
            />
          )}

          {currentTab === 'upload' && (
            <UploadReportView
              patient={selectedPatient}
              onUploadFile={handleUploadFile}
              onPasteText={handlePasteText}
              onProcessReport={handleProcessReport}
              onProcessingComplete={handleProcessingComplete}
              onNavigate={setCurrentTab}
              onStartNewIntake={() => setCurrentTab('patient-intake')}
            />
          )}

          {currentTab === 'results' && (
            <LabResultsView
              reports={reports}
              selectedReportId={selectedReportId}
              onSelectReportId={setSelectedReportId}
              onOpenProvenance={handleOpenProvenance}
              onOpenEdit={(r) => setEditModalResult(r)}
              onVerifyResult={handleVerifyResult}
            />
          )}

          {currentTab === 'conflicts' && (
            <ConflictsView
              conflicts={conflicts}
              onResolveConflict={handleResolveConflict}
            />
          )}

          {currentTab === 'comparison' && (
            <ComparisonView
              reports={reports}
              comparison={comparison}
              onSelectReports={handleSelectReportsForComparison}
              onNavigate={setCurrentTab}
            />
          )}

          {currentTab === 'insights' && (
            <InsightsView
              report={currentReport}
              insight={currentInsight}
              onGenerateInsights={handleGenerateInsights}
            />
          )}

          {currentTab === 'clarifications' && (
            <ClarificationsView
              questions={questions}
              onAnswerQuestion={handleAnswerQuestion}
            />
          )}

          {currentTab === 'review' && (
            <ReviewCenterView
              report={currentReport}
              reviewHistory={reviewHistory}
              onSubmitReview={handleSubmitReview}
            />
          )}
        </main>
      </div>

      {/* Modals */}
      {provenanceModalResult && (
        <ProvenanceModal
          labResult={provenanceModalResult}
          provenance={provenanceData}
          onClose={() => setProvenanceModalResult(null)}
          onVerifyResult={handleVerifyResult}
        />
      )}

      {editModalResult && (
        <EditLabResultModal
          labResult={editModalResult}
          onClose={() => setEditModalResult(null)}
          onSave={handleSaveLabResult}
        />
      )}
    </div>
  );
};

export default App;
