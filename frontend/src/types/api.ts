export interface HazardBoundingBox {
  label: string;
  ymin: number;
  xmin: number;
  ymax: number;
  xmax: number;
}

export type MtoClassification = "Human" | "Technology" | "Organisation";

export interface IncidentReport {
  id: number;
  created_at: string;
  raw_text: string;
  title: string;
  description: string;
  hazard_category: string;
  hazards_detected: HazardBoundingBox[];
  five_whys: string[];
  mto_classification: MtoClassification;
  hierarchy_of_controls_recommendation: string;
  cited_regulation_snippets: string[];
}

export interface ReportResponse {
  report: IncidentReport;
  annotated_image_base64: string | null;
}
