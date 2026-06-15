export type Severity = "severe" | "high" | "moderate" | "localized" | "none_reported";

export interface RiskItem {
  contaminant_id: string;
  name: string;
  severity: Severity;
  in_your_district: boolean;
  exceeds_limit_text: string;
  health_effects: string;
  vulnerable: string[];
  boiling_helps: boolean;
  removal: string;
  notable_districts: string[];
  affected_habitations: number | null;
  affected_population: number | null;
  source: string;
}

export interface RiskReport {
  state: string;
  district_query: string | null;
  overall_severity: Severity;
  headline: string;
  summary: string;
  boiling_warning: string | null;
  recommended_filter: string | null;
  risks: RiskItem[];
  note: string | null;
  disclaimer: string;
}

export interface StateSummary {
  state: string;
  state_code: string;
  contaminant_count: number;
  worst_severity: Severity;
  contaminants: string[];
}
