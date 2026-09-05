export interface User {
  id: number;
  email: string;
  full_name?: string;
  role: string;
}

export interface AuthState {
  user: User | null;
  token: string | null;
}

export interface PatientIntake {
  id?: number;
  patient_id?: number;
  symptoms?: string;
  existing_conditions?: string;
  allergies?: string;
  medications?: string;
  notes?: string;
  updated_at?: string;
}

export interface LabResult {
  id: number;
  report_id: number;
  original_name: string;
  canonical_name: string;
  observed_value: string;
  value_numeric?: number | null;
  unit?: string | null;
  reference_range_text?: string | null;
  reference_low?: number | null;
  reference_high?: number | null;
  reference_status: 'BELOW' | 'WITHIN' | 'ABOVE' | 'UNKNOWN' | 'LOW' | 'HIGH' | 'NORMAL';
  confidence?: number | null;
  source_text?: string | null;
  page_number?: number | null;
  verified: boolean;
  created_at: string;
}

export interface Report {
  id: number;
  patient_id: number;
  report_type?: string | null;
  original_filename?: string | null;
  mime_type?: string | null;
  report_date?: string | null;
  source_name?: string | null;
  processing_status: 'UPLOADED' | 'PROCESSING' | 'EXTRACTED' | 'VALIDATED' | 'FAILED' | 'REVIEW_REQUIRED';
  extraction_version?: string | null;
  created_at: string;
  updated_at: string;
  lab_results: LabResult[];
}

export interface PatientCreate {
  name: string;
  age?: number | null;
  sex?: 'MALE' | 'FEMALE' | 'OTHER' | 'UNKNOWN' | string;
  identifier?: string | null;
  symptoms?: string | null;
  existing_conditions?: string | null;
  allergies?: string | null;
  medications?: string | null;
  notes?: string | null;
}

export interface Patient {
  id: number;
  owner_user_id: number;
  identifier?: string | null;
  name: string;
  age?: number | null;
  sex: 'MALE' | 'FEMALE' | 'OTHER' | 'UNKNOWN';
  created_at: string;
  updated_at: string;
  intake?: PatientIntake | null;
  reports?: Report[];
  report_count?: number;
  active_conflict_count?: number;
  latest_report_date?: string | null;
}

export interface Conflict {
  id: number;
  patient_id: number;
  report_id?: number | null;
  conflict_type: 'ALLERGY' | 'MEDICATION' | 'DEMOGRAPHIC' | 'DUPLICATE';
  severity: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';
  description: string;
  source_a?: string | null;
  source_b?: string | null;
  status: 'OPEN' | 'ACKNOWLEDGED' | 'RESOLVED' | 'DISMISSED';
  resolution_notes?: string | null;
  created_at: string;
}

export interface ClarificationQuestion {
  id: number;
  patient_id: number;
  report_id?: number | null;
  question: string;
  reason?: string | null;
  category?: string | null;
  priority?: number;
  status: 'PENDING' | 'ANSWERED' | 'DISMISSED';
  answered: boolean;
  answer?: string | null;
  answered_by?: number | null;
  answered_at?: string | null;
  created_at: string;
}

export interface ComparisonResultItem {
  id: number;
  comparison_id?: number;
  parameter_name?: string;
  canonical_name: string;
  previous_value?: string | null;
  previous_value_numeric?: number | null;
  current_value?: string | null;
  current_value_numeric?: number | null;
  unit?: string | null;
  previous_unit?: string | null;
  current_unit?: string | null;
  previous_reference_range?: string | null;
  current_reference_range?: string | null;
  change_delta?: number | null;
  absolute_change?: number | null;
  change_percent?: number | null;
  percentage_change?: number | null;
  change_direction?: 'INCREASED' | 'DECREASED' | 'UNCHANGED' | 'NEW' | 'UNKNOWN' | 'STABLE' | 'MISSING' | 'NOT_COMPARABLE' | string;
  direction?: 'INCREASED' | 'DECREASED' | 'UNCHANGED' | 'NEW' | 'UNKNOWN' | 'STABLE' | 'MISSING' | 'NOT_COMPARABLE' | string;
  is_significant?: boolean;
}

export interface Comparison {
  id: number;
  patient_id: number;
  previous_report_id: number;
  current_report_id: number;
  created_at: string;
  results: ComparisonResultItem[];
}

export interface Insight {
  id: number;
  patient_id: number;
  report_id?: number | null;
  summary: string;
  key_findings: string[] | string;
  confidence?: number | null;
  model_used?: string | null;
  prompt_version?: string | null;
  created_at: string;
}

export interface Provenance {
  id: number;
  report_id: number;
  target_type: string;
  target_id: number;
  source_field: string;
  source_text_snippet: string;
  page_number?: number | null;
  confidence?: number | null;
  created_at: string;
}

export interface ReviewHistoryItem {
  id: number;
  report_id: number;
  reviewer_user_id: number;
  previous_status?: string | null;
  new_status: 'PENDING' | 'ACCEPTED' | 'FLAGGED' | 'REJECTED';
  notes?: string | null;
  created_at: string;
}

export interface DashboardStats {
  total_patients: number;
  total_reports: number;
  total_lab_results: number;
  within_range: number;
  below_range: number;
  above_range: number;
  unknown_range: number;
  open_conflicts: number;
  pending_questions: number;
  unverified_results: number;
  verified_results: number;
  recent_activity?: Array<{
    type: string;
    description: string;
    timestamp: string;
  }>;
}

export interface TrendPoint {
  date: string;
  value: number;
  unit: string;
  reference_low?: number;
  reference_high?: number;
}
