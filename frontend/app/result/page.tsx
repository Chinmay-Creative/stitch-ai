"use client";

import { useEffect, useState } from "react";
import { Download, Loader2, Send } from "lucide-react";
import Link from "next/link";
import { downloadFile, getAIStatus, getPreviewUrl, getStitchInfo, sendFeedback } from "@/lib/api";
import type { AIStatusResponse, FeedbackResponse } from "@/lib/types";

type ChatExchange = {
  role: "user" | "ai";
  message: string;
};

type StitchInfo = {
  stitch_estimate?: number;
};

export default function ResultPage() {
  const [jobId] = useState(() => (typeof window === "undefined" ? null : sessionStorage.getItem("job_id")));
  const [aiStatus, setAIStatus] = useState<AIStatusResponse | null>(null);
  const [stitchInfo, setStitchInfo] = useState<StitchInfo | null>(null);
  const [message, setMessage] = useState("");
  const [chatHistory, setChatHistory] = useState<ChatExchange[]>([]);
  const [isSending, setIsSending] = useState(false);
  const [feedbackError, setFeedbackError] = useState("");
  const [downloadError, setDownloadError] = useState("");

  useEffect(() => {
    getAIStatus()
      .then(setAIStatus)
      .catch(() => setAIStatus({ enabled: false, provider: "unknown", ready: false }));

    if (jobId) {
      getStitchInfo(jobId).then(setStitchInfo);
    }
  }, [jobId]);

  async function handleDownload(format: "dst" | "pes") {
    if (jobId) {
      try {
        setDownloadError("");
        await downloadFile(jobId, format);
      } catch {
        setDownloadError(`We could not download the ${format.toUpperCase()} file yet. Please try again in a moment.`);
      }
    }
  }

  async function handleFeedback() {
    if (!jobId || !message.trim()) {
      return;
    }

    try {
      setIsSending(true);
      setFeedbackError("");
      const userMessage = message.trim();
      setMessage("");
      setChatHistory((current) => [...current, { role: "user", message: userMessage }]);
      const response: FeedbackResponse = await sendFeedback(jobId, userMessage);
      setChatHistory((current) => [
        ...current,
        { role: "ai", message: response.message ?? response.status ?? "Feedback received. We will use it to improve this design." },
      ]);
    } catch (error) {
      setFeedbackError(error instanceof Error ? error.message : "Could not send feedback.");
    } finally {
      setIsSending(false);
    }
  }

  return (
    <div className="min-h-[calc(100vh-4rem)] bg-white px-4 py-12 sm:px-6 lg:px-8">
      <div className="mx-auto grid max-w-7xl gap-8 lg:grid-cols-[60fr_40fr]">
        <section>
          <h1 className="text-4xl font-bold tracking-tight text-slate-950">Your design is ready</h1>
          <div className="mt-8 rounded-2xl border border-slate-200 bg-white p-3 shadow-sm">
            <img
              src={jobId ? getPreviewUrl(jobId) : ""}
              alt="Generated embroidery design preview"
              className="aspect-[4/3] w-full rounded-xl border border-slate-100 object-contain"
            />
          </div>
        </section>

        <aside className="space-y-6">
          <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
            <h2 className="text-xl font-bold text-slate-950">Download your files</h2>
            <div className="mt-5 grid grid-cols-2 gap-3">
              <button
                type="button"
                onClick={() => void handleDownload("dst")}
                className="inline-flex h-11 items-center justify-center gap-2 rounded-md border border-[#6366f1] bg-white px-4 text-sm font-semibold text-[#6366f1] hover:bg-indigo-50"
              >
                <Download className="h-4 w-4" aria-hidden="true" />
                Download DST
              </button>
              <button
                type="button"
                onClick={() => void handleDownload("pes")}
                className="inline-flex h-11 items-center justify-center gap-2 rounded-md border border-[#6366f1] bg-white px-4 text-sm font-semibold text-[#6366f1] hover:bg-indigo-50"
              >
                <Download className="h-4 w-4" aria-hidden="true" />
                Download PES
              </button>
            </div>
            <p className="mt-5 text-sm text-slate-500">
              {stitchInfo?.stitch_estimate
                ? `Estimated stitches: ${stitchInfo.stitch_estimate.toLocaleString()}`
                : stitchInfo === null
                ? "Estimated stitches: calculating..."
                : "Stitch info unavailable"}
            </p>
            {downloadError ? <p className="mt-3 text-sm font-medium text-red-600">{downloadError}</p> : null}
          </section>

          <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
            <h2 className="text-xl font-bold text-slate-950">Improve with AI</h2>
            {aiStatus?.enabled ? (
              <>
                <textarea
                  value={message}
                  onChange={(event) => setMessage(event.target.value)}
                  rows={5}
                  className="mt-5 w-full rounded-lg border border-slate-300 p-3 text-sm text-slate-900 outline-none focus:border-[#6366f1] focus:ring-2 focus:ring-indigo-100"
                  placeholder="Describe any issues..."
                />
                <button
                  type="button"
                  onClick={() => void handleFeedback()}
                  disabled={isSending || !message.trim()}
                  className="mt-3 inline-flex h-10 items-center justify-center gap-2 rounded-md bg-[#6366f1] px-4 text-sm font-semibold text-white hover:bg-[#5558e6] disabled:cursor-not-allowed disabled:bg-slate-300"
                >
                  {isSending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
                  Send
                </button>
                {feedbackError ? <p className="mt-3 text-sm font-medium text-red-600">{feedbackError}</p> : null}
                <div className="mt-5 space-y-3">
                  {chatHistory.map((chat, index) => (
                    <div
                      key={`${chat.role}-${index}`}
                      className={`rounded-lg p-3 text-sm ${
                        chat.role === "user" ? "bg-indigo-50 text-slate-900" : "bg-slate-50 text-slate-700"
                      }`}
                    >
                      <p className="font-semibold">{chat.role === "user" ? "You" : "StitchAI"}</p>
                      <p className="mt-1">{chat.message}</p>
                    </div>
                  ))}
                </div>
              </>
            ) : (
              <p className="mt-5 text-sm text-slate-500">AI feedback coming soon</p>
            )}
          </section>

          <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
            <h2 className="text-xl font-bold text-slate-950">Actions</h2>
            <Link
              href="/upload"
              className="mt-5 inline-flex h-11 w-full items-center justify-center rounded-md bg-[#6366f1] px-4 text-sm font-semibold text-white hover:bg-[#5558e6]"
            >
              Process another design
            </Link>
          </section>
        </aside>
      </div>
    </div>
  );
}
