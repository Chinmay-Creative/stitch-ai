export interface UploadResponse {
  job_id: string;
  filename: string;
  size: number;
}

export interface ProcessRequest {
  job_id: string;
}

export interface ProcessResponse {
  job_id?: string;
  status: string;
}

export interface StatusResponse {
  job_id?: string;
  status: "queued" | "processing" | "complete" | "completed" | "ready" | "error" | "failed" | string;
  step?: number;
  progress?: number;
  message?: string;
  preview_url?: string;
}

export interface FeedbackRequest {
  job_id: string;
  message: string;
}

export interface FeedbackResponse {
  status: string;
  job_id?: string;
  message?: string;
}

export interface AIStatusResponse {
  enabled: boolean;
  provider: string;
  ready: boolean;
}

export interface ExportResponse {
  status: string;
  job_id?: string;
  format?: string;
}
