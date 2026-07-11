const BASE = "http://localhost:8000";

export interface Plume {
  plume_id: string;
  lat: number;
  lon: number;
  leak_rate_kg_hr: number;
  detected_date: string;
  state: string;
  place: string;
  source: string;
  wind_speed_kmh: number;
  wind_dir_deg: number;
}

// Backend serves full state names ("New Mexico" / "Texas" / "Oklahoma");
// the UI keys colors and CSS classes off the two-letter abbreviation.
export function stateAbbr(state: string): "NM" | "TX" | "OK" {
  if (state === "New Mexico") return "NM";
  if (state === "Oklahoma") return "OK";
  return "TX";
}

/** A plume a resident reports manually (not from satellite data). Client-side
 * only — plotted as a red dot for the session; not persisted to the backend. */
export interface ReportedPlume {
  id: string;
  lat: number;
  lon: number;
  smell: boolean;
  visible_flare: boolean;
  notes: string;
}

export interface Regulator {
  regulator_name: string;
  complaint_mechanism: string;
  applicable_rule: string;
  rule_summary: string;
}

export interface Attribution {
  plume_id: string;
  plume_lat: number;
  plume_lon: number;
  leak_rate_kg_hr: number;
  detected_date: string;
  state: string;
  source: string;
  matched: boolean;
  nearest_distance_m: number;
  operator: string | null;
  facility_id: string | null;
  facility_name: string | null;
  facility_lat: number | null;
  facility_lon: number | null;
  distance_m: number | null;
  confidence: number | null;
  confidence_method: "trained_model" | "hand_tuned_fallback" | null;
  regulator: Regulator;
  display_statement: string;
}

export interface ReportSummary {
  plume_id: string;
  reports: GroundTruthReport[];
  count: number;
  confidence_bump: number;
}

export interface GroundTruthReport {
  name: string;
  zip_code: string;
  smell: boolean;
  visible_flare: boolean;
  notes: string;
  lat: number | null;
  lon: number | null;
  submitted_at?: string;
}

/** Resident-entered observations that ground a citizen-report letter. */
export interface CitizenReportInput {
  name: string;
  zip_code: string;
  smell: boolean;
  visible_flare: boolean;
  notes: string;
}

export interface CosignSummary {
  plume_id: string;
  count: number;
  signers: { name: string; zip: string; signed_at: string }[];
}

async function json<T>(res: Response): Promise<T> {
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  return res.json();
}

export const api = {
  events: () =>
    fetch(`${BASE}/events`).then(json<{ events: Plume[] }>),

  attribution: (plumeId: string) =>
    fetch(`${BASE}/attribution/${encodeURIComponent(plumeId)}`).then(
      json<Attribution>,
    ),

  generateComplaint: (
    plumeId: string,
    cosignCount: number,
    citizenReport?: CitizenReportInput,
  ) =>
    fetch(`${BASE}/complaint/generate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        plume_id: plumeId,
        cosign_count: cosignCount,
        citizen_report: citizenReport ?? null,
      }),
    }).then(json<{ letter: string; generator: string }>),

  reports: (plumeId: string) =>
    fetch(`${BASE}/community/reports?plume_id=${encodeURIComponent(plumeId)}`).then(
      json<ReportSummary>,
    ),

  submitReport: (report: GroundTruthReport & { plume_id: string }) =>
    fetch(`${BASE}/community/reports`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(report),
    }).then(json<ReportSummary>),

  cosigns: (plumeId: string) =>
    fetch(`${BASE}/community/cosign?plume_id=${encodeURIComponent(plumeId)}`).then(
      json<CosignSummary>,
    ),

  cosign: (plumeId: string, name: string, zipCode: string) =>
    fetch(`${BASE}/community/cosign`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ plume_id: plumeId, name, zip_code: zipCode }),
    }).then(json<CosignSummary>),
};
