export type JsonObject = Record<string, unknown>;

export type RunStatus =
  | "created"
  | "running"
  | "pending_approval"
  | "completed"
  | "rejected"
  | "failed";

export interface RunDetail {
  id: number;
  repo_path: string | null;
  repo_url: string | null;
  user_task: string;
  expected_behavior: string | null;
  test_command: string | null;
  status: RunStatus;
  current_node: string | null;
  final_report: string | null;
  approval_payload: JsonObject | null;
  approval_status: string | null;
  patch_diff: string | null;
  test_result: JsonObject | null;
  verification_result: JsonObject | null;
  risk_score: JsonObject | null;
  error_message: string | null;
  created_at: string;
  updated_at: string;
}

export interface RunStartResponse {
  id: number;
  status: RunStatus;
  current_node: string | null;
  has_final_report: boolean;
  repo_path: string | null;
  repo_url: string | null;
  final_report: string | null;
  approval_status: string | null;
  patch_diff: string | null;
  test_result: JsonObject | null;
  verification_result: JsonObject | null;
  risk_score: JsonObject | null;
  error_message: string | null;
  approval_payload: JsonObject | null;
}

export interface RunEvent {
  id: number;
  run_id: number;
  event_type: string;
  title: string;
  message: string | null;
  payload: JsonObject | null;
  created_at: string;
}

export interface RunCreatePayload {
  repo_path?: string;
  repo_url?: string;
  user_task: string;
  expected_behavior?: string;
  test_command?: string;
}
