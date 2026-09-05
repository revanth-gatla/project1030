import {
  User,
  Patient,
  PatientIntake,
  Report,
  LabResult,
  Conflict,
  ClarificationQuestion,
  Comparison,
  Insight,
  Provenance,
  ReviewHistoryItem,
  DashboardStats,
  TrendPoint,
} from '../types';

const API_BASE = import.meta.env.VITE_API_URL || 'https://project1030.onrender.com';

class ApiClient {
  private token: string | null = localStorage.getItem('medlens_token');

  setToken(token: string | null) {
    this.token = token;
    if (token) {
      localStorage.setItem('medlens_token', token);
    } else {
      localStorage.removeItem('medlens_token');
    }
  }

  getToken(): string | null {
    return this.token;
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const headers: Record<string, string> = {
      ...(options.headers as Record<string, string>),
    };

    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }

    if (!(options.body instanceof FormData) && !headers['Content-Type']) {
      headers['Content-Type'] = 'application/json';
    }

    const response = await fetch(`${API_BASE}${endpoint}`, {
      ...options,
      headers,
    });

    if (!response.ok) {
      if (response.status === 401) {
        this.setToken(null);
        localStorage.removeItem('medlens_token');
        window.dispatchEvent(new Event('medlens_unauthorized'));
      }
      let errorMessage = 'Request failed';
      try {
        const errorData = await response.json();
        if (errorData.error?.message) {
          errorMessage = errorData.error.message;
        } else if (typeof errorData.detail === 'string') {
          errorMessage = errorData.detail;
        } else if (Array.isArray(errorData.detail) && errorData.detail.length > 0) {
          const first = errorData.detail[0];
          if (first.loc && first.loc.includes('email')) {
            errorMessage = 'Please enter a valid email address.';
          } else {
            errorMessage = first.msg || 'Validation failed.';
          }
        } else {
          errorMessage = response.statusText || 'Request failed';
        }
      } catch {
        errorMessage = `HTTP error ${response.status}: ${response.statusText}`;
      }
      throw new Error(errorMessage);
    }

    // 204 No Content
    if (response.status === 204) {
      return {} as T;
    }

    return response.json();
  }

  // Auth
  async login(email: string, password: string): Promise<{ access_token: string; user?: User }> {
    const res = await this.request<{ access_token: string; user?: User }>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
    this.setToken(res.access_token);
    return res;
  }

  async register(email: string, password: string): Promise<{ access_token: string; user?: User }> {
    const res = await this.request<{ access_token: string; user?: User }>('/auth/register', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
    this.setToken(res.access_token);
    return res;
  }

  async getMe(): Promise<User> {
    return this.request<User>('/auth/me');
  }

  // Demo Seed
  async seedDemo(): Promise<{ status: string; email: string; password: string }> {
    return this.request<{ status: string; email: string; password: string }>('/demo/seed', {
      method: 'POST',
    });
  }

  // Patients
  async getPatients(): Promise<Patient[]> {
    return this.request<Patient[]>('/patients');
  }

  async getPatient(id: number): Promise<Patient> {
    return this.request<Patient>(`/patients/${id}`);
  }

  async createPatient(data: import('../types').PatientCreate): Promise<Patient> {
    return this.request<Patient>('/patients', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async updateIntake(patientId: number, intake: PatientIntake): Promise<PatientIntake> {
    return this.request<PatientIntake>(`/patients/${patientId}/intake`, {
      method: 'PUT',
      body: JSON.stringify(intake),
    });
  }

  // Reports
  async uploadReport(patientId: number, file: File, reportDate?: string, sourceName?: string): Promise<Report> {
    const formData = new FormData();
    formData.append('file', file);
    if (reportDate) formData.append('report_date', reportDate);
    if (sourceName) formData.append('source_name', sourceName);
    return this.request<Report>(`/patients/${patientId}/reports`, {
      method: 'POST',
      body: formData,
    });
  }

  async pasteReport(patientId: number, data: { text: string; report_date?: string; source_name?: string }): Promise<Report> {
    return this.request<Report>(`/patients/${patientId}/reports/paste`, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async processReport(reportId: number): Promise<Report> {
    return this.request<Report>(`/reports/${reportId}/process`, {
      method: 'POST',
    });
  }

  async getReport(reportId: number): Promise<Report> {
    return this.request<Report>(`/reports/${reportId}`);
  }

  async getPatientReports(patientId: number): Promise<Report[]> {
    return this.request<Report[]>(`/patients/${patientId}/reports`);
  }

  async updateLabResult(labResultId: number, update: Partial<LabResult>): Promise<LabResult> {
    return this.request<LabResult>(`/lab-results/${labResultId}`, {
      method: 'PATCH',
      body: JSON.stringify(update),
    });
  }

  async generateInsights(reportId: number): Promise<Insight> {
    return this.request<Insight>(`/reports/${reportId}/insights`, {
      method: 'POST',
    });
  }

  // Analysis & Intelligence
  async getConflicts(patientId: number): Promise<Conflict[]> {
    return this.request<Conflict[]>(`/patients/${patientId}/conflicts`);
  }

  async resolveConflict(conflictId: number, notes?: string): Promise<Conflict> {
    return this.request<Conflict>(`/conflicts/${conflictId}/resolve`, {
      method: 'POST',
      body: JSON.stringify({ resolution_notes: notes || 'Resolved by clinician.' }),
    });
  }

  async getQuestions(patientId: number): Promise<ClarificationQuestion[]> {
    return this.request<ClarificationQuestion[]>(`/patients/${patientId}/clarification-questions`);
  }

  async answerQuestion(questionId: number, answer: string): Promise<ClarificationQuestion> {
    return this.request<ClarificationQuestion>(`/clarification-questions/${questionId}/answer`, {
      method: 'POST',
      body: JSON.stringify({ answer }),
    });
  }

  async getComparison(patientId: number, previousReportId: number, currentReportId: number): Promise<Comparison> {
    return this.request<Comparison>(`/patients/${patientId}/comparisons?previous_report_id=${previousReportId}&current_report_id=${currentReportId}`);
  }

  async getProvenance(reportId: number): Promise<Provenance[]> {
    return this.request<Provenance[]>(`/reports/${reportId}/provenance`);
  }

  async submitReview(reportId: number, data: { status: string; notes?: string }): Promise<ReviewHistoryItem> {
    return this.request<ReviewHistoryItem>(`/reports/${reportId}/review`, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async getReviewHistory(patientId: number): Promise<ReviewHistoryItem[]> {
    return this.request<ReviewHistoryItem[]>(`/patients/${patientId}/review-history`);
  }

  async getDashboardStats(): Promise<DashboardStats> {
    return this.request<DashboardStats>('/dashboard/stats');
  }

  async getTrends(patientId: number, parameter: string): Promise<TrendPoint[]> {
    return this.request<TrendPoint[]>(`/patients/${patientId}/trends?parameter=${encodeURIComponent(parameter)}`);
  }

  async downloadPatientReport(patientId: number): Promise<Blob> {
    const headers: Record<string, string> = {};
    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }
    const response = await fetch(`${API_BASE}/patients/${patientId}/report/pdf`, {
      headers,
    });
    if (!response.ok) {
      throw new Error(`Failed to generate PDF report (${response.status}): ${response.statusText}`);
    }
    return response.blob();
  }
}


export const api = new ApiClient();
