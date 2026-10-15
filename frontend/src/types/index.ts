/**
 * Types mirroring the backend API contract in `docs/05-api-contract.md`.
 *
 * These are hand-written rather than generated so the compiler catches
 * contract drift at build time: if the backend changes a field, the frontend
 * fails to compile rather than failing silently at runtime.
 */

export type MatchStatus = 'matched' | 'partial' | 'missing';
export type RequirementLevel = 'required' | 'preferred';
export type Priority = 'high' | 'medium' | 'low';
export type RecommendationSource = 'rule' | 'ai';
export type AiStatus = 'available' | 'unavailable';

export interface User {
  id: string;
  full_name: string;
  email: string;
  created_at: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: User;
}

export interface ApiErrorBody {
  error: {
    code: string;
    what: string;
    why: string;
    next_step: string;
    request_id: string;
    fields?: Record<string, string>;
  };
}

export interface SkillMatch {
  skill_name: string;
  match_status: MatchStatus;
  requirement_level: RequirementLevel;
  matched_via: string | null;
  evidence_snippet: string | null;
}

export interface ScoreCategory {
  category_key: string;
  category_name: string;
  weight: number;
  points_earned: number;
  points_possible: number;
  explanation: string;
  evidence: Array<Record<string, unknown>>;
  recommendation: string | null;
  limitation: string;
}

export interface ResumeSectionResult {
  section_key: string;
  detected: boolean;
  matched_heading: string | null;
  note: string;
}

export interface StatementFinding {
  statement_text: string;
  issue_codes: string[];
  word_count: number;
  has_measurable_result: boolean;
  suggestion: string | null;
}

export interface StatementSummary {
  total_bullets: number;
  with_measurable_result: number;
  action_verb_rate: number;
  findings: StatementFinding[];
}

export interface Recommendation {
  priority: Priority;
  source: RecommendationSource;
  category: string;
  title: string;
  detail: string;
}

export interface JobAnalysis {
  job_title: string | null;
  company_name: string | null;
  min_years_experience: number | null;
  required_education_level: string | null;
  requirement_split_inferred: boolean;
  required_skills: string[];
  preferred_skills: string[];
}

export interface AnalysisSummary {
  id: string;
  title: string;
  job_title: string | null;
  overall_score: number;
  created_at: string;
}

export interface AnalysisDetail {
  id: string;
  title: string;
  resume_filename: string;
  created_at: string;
  overall_score: number;
  disclaimer: string;
  evidence_warnings?: string[];
  score_breakdown: ScoreCategory[];
  skills: {
    matched: SkillMatch[];
    partial: SkillMatch[];
    missing: SkillMatch[];
  };
  sections: ResumeSectionResult[];
  statements: StatementSummary;
  job_analysis: JobAnalysis;
  recommendations: Recommendation[];
  ai_status: AiStatus;
  ai_reason_code: string | null;
  ai_message: string;
}

export interface AnalysisList {
  items: AnalysisSummary[];
  total: number;
  page: number;
  page_size: number;
  has_next: boolean;
}

export interface DashboardStats {
  total_analyses: number;
  average_score: number | null;
  best_score: number | null;
  analyses_this_month: number;
  score_trend: Array<{ date: string; score: number }>;
  common_missing_skills: Array<{ skill: string; occurrences: number }>;
}
