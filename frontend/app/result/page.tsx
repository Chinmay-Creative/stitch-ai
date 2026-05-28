"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Navbar from "@/components/layout/Navbar";
import {
  downloadFile,
  getAIStatus,
  getPreviewUrl,
  getStitchInfo,
  sendFeedback,
} from "@/lib/api";

export default function ResultPage() {
  const router = useRouter();
  const [mounted, setMounted] = useState(false);
  const [jobId, setJobId] = useState<string | null>(null);
  const [aiEnabled, setAiEnabled] = useState(false);
  const [feedbackMessage, setFeedbackMessage] = useState("");
  const [chatHistory, setChatHistory] = useState<{ role: string; text: string }[]>([]);
  const [sending, setSending] = useState(false);
  const [stitchInfo, setStitchInfo] = useState<any>(null);
  const [downloading, setDownloading] = useState<string | null>(null);

  useEffect(() => {
    const id = sessionStorage.getItem("job_id");
    setJobId(id);
    setMounted(true);

    if (id) {
      getAIStatus().then((status) => setAiEnabled(status?.enabled === true));
      getStitchInfo(id).then((info) => setStitchInfo(info));
    }
  }, []);

  const handleDownload = async (format: "dst" | "pes") => {
    if (!jobId) return;
    setDownloading(format);
    try {
      await downloadFile(jobId, format);
    } catch {
      alert("Download failed. Please try again.");
    } finally {
      setDownloading(null);
    }
  };

  const handleFeedback = async () => {
    if (!feedbackMessage.trim() || !jobId) return;
    setSending(true);
    const userMsg = feedbackMessage;
    setFeedbackMessage("");
    setChatHistory((prev) => [...prev, { role: "user", text: userMsg }]);
    try {
      const result = await sendFeedback(jobId, userMsg);
      const aiMsg = result?.user_message || "Feedback noted. This will improve future designs.";
      setChatHistory((prev) => [...prev, { role: "ai", text: aiMsg }]);
    } catch {
      setChatHistory((prev) => [...prev, { role: "ai", text: "Could not process feedback. Please try again." }]);
    } finally {
      setSending(false);
    }
  };

  if (!mounted) return null;

  return (
    <div className="min-h-screen bg-white">
      <Navbar />
      <div className="mx-auto grid max-w-6xl grid-cols-1 gap-8 px-4 py-12 lg:grid-cols-[1fr_400px]">
        <section>
          <h1 className="text-4xl font-bold tracking-tight text-slate-950">Your design is ready</h1>
          <div className="mt-8 rounded-2xl border border-slate-200 bg-white p-3 shadow-sm">
            {jobId ? (
              <img
                src={getPreviewUrl(jobId)}
                alt="Generated embroidery design preview"
                className="aspect-[4/3] w-full rounded-xl border border-slate-100 object-contain"
              />
            ) : (
              <div className="aspect-[4/3] w-full rounded-xl border border-slate-100 bg-slate-50 animate-pulse" />
            )}
          </div>
        </section>

        <aside className="flex flex-col gap-6">
          <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
            <h2 className="text-lg font-semibold text-slate-900">Download your files</h2>
            <div className="mt-4 flex gap-3">
              <button
                onClick={() => handleDownload("dst")}
                disabled={!!downloading}
                className="flex flex-1 items-center justify-center gap-2 rounded-xl border border-indigo-300 px-4 py-2.5 text-sm font-medium text-indigo-600 hover:bg-indigo-50 disabled:opacity-50"
              >
                {downloading === "dst" ? "..." : "⬇ Download DST"}
              </button>
              <button
                onClick={() => handleDownload("pes")}
                disabled={!!downloading}
                className="flex flex-1 items-center justify-center gap-2 rounded-xl border border-indigo-300 px-4 py-2.5 text-sm font-medium text-indigo-600 hover:bg-indigo-50 disabled:opacity-50"
              >
                {downloading === "pes" ? "..." : "⬇ Download PES"}
              </button>
            </div>
            <p className="mt-2 text-sm text-slate-500">
              {stitchInfo?.stitch_estimate
                ? `Estimated stitches: ${stitchInfo.stitch_estimate.toLocaleString()}`
                : "Estimated stitches: calculating..."}
            </p>
          </div>

          <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
            <h2 className="text-lg font-semibold text-slate-900">Improve with AI</h2>
            {aiEnabled ? (
              <div className="mt-4 flex flex-col gap-3">
                <div className="flex flex-col gap-2 max-h-48 overflow-y-auto">
                  {chatHistory.map((msg, i) => (
                    <div
                      key={i}
                      className={`rounded-xl px-4 py-2.5 text-sm ${
                        msg.role === "user"
                          ? "bg-indigo-50 text-slate-800 self-end"
                          : "bg-slate-100 text-slate-700 self-start"
                      }`}
                    >
                      <span className="font-medium block mb-1">{msg.role === "user" ? "You" : "StitchAI"}</span>
                      {msg.text}
                    </div>
                  ))}
                </div>
                <textarea
                  value={feedbackMessage}
                  onChange={(e) => setFeedbackMessage(e.target.value)}
                  placeholder="Describe any issues..."
                  className="w-full rounded-xl border border-slate-200 p-3 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-indigo-300"
                  rows={3}
                />
                <button
                  onClick={handleFeedback}
                  disabled={sending || !feedbackMessage.trim()}
                  className="flex items-center justify-center gap-2 rounded-xl bg-indigo-600 px-4 py-2.5 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
                >
                  {sending ? "Sending..." : "✈ Send"}
                </button>
              </div>
            ) : (
              <p className="mt-3 text-sm text-slate-400">AI feedback coming soon</p>
            )}
          </div>

          <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
            <h2 className="text-lg font-semibold text-slate-900">Actions</h2>
            <button
              onClick={() => router.push("/upload")}
              className="mt-4 w-full rounded-xl bg-indigo-600 px-4 py-2.5 text-sm font-medium text-white hover:bg-indigo-700"
            >
              Process another design
            </button>
          </div>
        </aside>
      </div>
    </div>
  );
}
