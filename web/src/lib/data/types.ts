export interface Facility {
  facility_id: string;
  facility_name: string;
  state: string;
  city_town: string;
  hospital_type: string;
  hospital_overall_rating: string;
  county_fips: string;
}

export interface QualityAnomaly {
  facility_id: string;
  measure_id: string;
  measure_name: string;
  score: string;
  z_score: number;
  severity: 'critical' | 'high' | 'medium';
  compared_to_national: string;
}

export interface CareGap {
  facility_id: string;
  facility_name: string;
  measure_name: string;
  excess_readmission_ratio: string;
  gap_type: string;
}

export interface KPIData {
  totalFacilities: number;
  avgStarRating: number;
  anomalyCount: number;
  careGapCount: number;
  highSVIFacilities: number;
  totalMeasures: number;
}

export interface BriefingData {
  executive_summary: string;
  key_findings: string[];
  anomalies_and_alerts: { facility: string; measure: string; severity: string; detail: string }[];
  equity_insights: string[];
  recommended_actions: { priority: string; action: string; rationale: string }[];
}
