"use client";

import { useState } from "react";
import { uploadImage } from "@/lib/api";

export default function DropZone() {
  const [status, setStatus] = useState("Waiting for an image");

  async function handleFile(file: File) {
    setStatus("Uploading...");
    const response = await uploadImage(file);
    setStatus(`Created job ${response.job_id} for ${response.filename}`);
  }

  return (
    <label className="flex min-h-64 cursor-pointer flex-col items-center justify-center rounded-lg border border-dashed border-neutral-300 bg-white p-8 text-center hover:border-neutral-500">
      <input
        type="file"
        accept="image/*"
        className="sr-only"
        onChange={(event) => {
          const file = event.target.files?.[0];
          if (file) {
            void handleFile(file);
          }
        }}
      />
      <span className="text-lg font-semibold text-neutral-950">Choose image</span>
      <span className="mt-2 text-sm text-neutral-600">{status}</span>
    </label>
  );
}
