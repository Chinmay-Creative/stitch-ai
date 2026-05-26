"use client";

import { useState } from "react";
import { sendFeedback } from "@/lib/api";

export default function FeedbackChat() {
  const [message, setMessage] = useState("");
  const [status, setStatus] = useState("Ready for feedback");

  async function submitFeedback() {
    if (!message.trim()) {
      return;
    }

    await sendFeedback("demo-job", message);
    setStatus("Feedback received");
    setMessage("");
  }

  return (
    <aside className="rounded-lg border border-neutral-200 bg-white p-5">
      <h2 className="text-lg font-semibold text-neutral-950">AI feedback</h2>
      <textarea
        value={message}
        onChange={(event) => setMessage(event.target.value)}
        rows={5}
        className="mt-4 w-full rounded-md border border-neutral-300 p-3 text-sm outline-none focus:border-neutral-950"
        placeholder="Ask for stitch density, color, or path changes."
      />
      <button
        type="button"
        onClick={() => void submitFeedback()}
        className="mt-3 h-10 rounded-md bg-neutral-950 px-4 text-sm font-semibold text-white hover:bg-neutral-800"
      >
        Send feedback
      </button>
      <p className="mt-3 text-sm text-neutral-600">{status}</p>
    </aside>
  );
}
