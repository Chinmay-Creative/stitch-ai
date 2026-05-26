const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function uploadImage(file: File): Promise<{ job_id: string; filename: string }> {
  const form = new FormData();
  form.append("file", file);
  const res = await fetch(`${API}/api/upload`, { method: "POST", body: form });
  if (!res.ok) throw new Error("Upload failed");
  return res.json();
}

export async function startProcessing(jobId: string): Promise<void> {
  const res = await fetch(`${API}/api/process`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ job_id: jobId }),
  });

  if (!res.ok) throw new Error("Could not start processing");
}

export async function pollStatus(jobId: string, onUpdate: (status: string) => void): Promise<string> {
  return new Promise((resolve) => {
    const interval = setInterval(async () => {
      try {
        const res = await fetch(`${API}/api/status/${jobId}`);
        const data = await res.json();
        onUpdate(data.status);
        if (data.status === "complete" || data.status === "error") {
          clearInterval(interval);
          resolve(data.status);
        }
      } catch {
        clearInterval(interval);
        resolve("error");
      }
    }, 2000);
  });
}

export async function sendFeedback(jobId: string, message: string) {
  const res = await fetch(`${API}/api/feedback`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ job_id: jobId, message }),
  });
  return res.json();
}

export async function getAIStatus() {
  try {
    const res = await fetch(`${API}/api/feedback/status`);
    return res.json();
  } catch {
    return { enabled: false, provider: "disabled", ready: false };
  }
}

export async function downloadFile(jobId: string, format: "dst" | "pes"): Promise<void> {
  const res = await fetch(`${API}/api/export/${jobId}/${format}`);
  if (!res.ok) throw new Error("Download failed");
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `stitchai_design.${format}`;
  a.click();
  URL.revokeObjectURL(url);
}

export function getPreviewUrl(jobId: string): string {
  return `${API}/api/preview/${jobId}/enhanced`;
}

export async function getStitchInfo(jobId: string) {
  try {
    const res = await fetch(`${API}/api/export/${jobId}/info`);
    return res.json();
  } catch {
    return null;
  }
}
