"use client";

import { useCallback, useEffect, useState } from "react";
import { useDropzone } from "react-dropzone";
import { ImageUp, Loader2 } from "lucide-react";
import { useRouter } from "next/navigation";
import { startProcessing, uploadImage } from "@/lib/api";

const ACCEPTED_TYPES = {
  "image/png": [".png"],
  "image/jpeg": [".jpg", ".jpeg"],
  "image/svg+xml": [".svg"],
};

function formatFileSize(bytes: number) {
  if (bytes < 1024 * 1024) {
    return `${(bytes / 1024).toFixed(1)} KB`;
  }

  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
}

export default function UploadPage() {
  const router = useRouter();
  const [file, setFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [error, setError] = useState("");
  const [isUploading, setIsUploading] = useState(false);

  useEffect(() => {
    return () => {
      if (previewUrl) {
        URL.revokeObjectURL(previewUrl);
      }
    };
  }, [previewUrl]);

  const onDrop = useCallback((acceptedFiles: File[], rejectedFiles: unknown[]) => {
    setError("");

    if (rejectedFiles.length > 0) {
      setFile(null);
      setPreviewUrl(null);
      setError("Please upload a PNG, JPG, or SVG image.");
      return;
    }

    const selectedFile = acceptedFiles[0];
    if (selectedFile) {
      if (previewUrl) {
        URL.revokeObjectURL(previewUrl);
      }

      setFile(selectedFile);
      setPreviewUrl(URL.createObjectURL(selectedFile));
    }
  }, [previewUrl]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: ACCEPTED_TYPES,
    multiple: false,
  });

  async function handleDigitize() {
    if (!file) {
      return;
    }

    try {
      setIsUploading(true);
      setError("");
      const response = await uploadImage(file);
      sessionStorage.setItem("job_id", response.job_id);
      await startProcessing(response.job_id);
      router.push("/processing");
    } catch (uploadError) {
      setError(uploadError instanceof Error ? uploadError.message : "Upload failed. Please try again.");
    } finally {
      setIsUploading(false);
    }
  }

  return (
    <div className="min-h-[calc(100vh-4rem)] bg-white px-4 py-12 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-3xl text-center">
        <h1 className="text-4xl font-bold tracking-tight text-slate-950">Upload your design</h1>
        <p className="mt-4 text-lg text-slate-600">Choose a PNG, JPG, or SVG image to digitize.</p>

        <div
          {...getRootProps()}
          className={`mt-10 flex min-h-80 cursor-pointer flex-col items-center justify-center rounded-2xl border-2 border-dashed bg-white p-8 transition ${
            isDragActive ? "border-[#6366f1] bg-indigo-50" : "border-slate-300 hover:border-[#6366f1]"
          }`}
        >
          <input {...getInputProps()} />
          {previewUrl ? (
            <div className="w-full">
              <img
                src={previewUrl}
                alt="Selected design preview"
                className="mx-auto max-h-60 max-w-full rounded-xl border border-slate-200 object-contain"
              />
              {file ? (
                <div className="mt-5 text-center">
                  <p className="font-semibold text-slate-950">{file.name}</p>
                  <p className="mt-1 text-sm text-slate-500">{formatFileSize(file.size)}</p>
                </div>
              ) : null}
            </div>
          ) : (
            <>
              <div className="flex h-16 w-16 items-center justify-center rounded-full bg-indigo-50">
                <ImageUp className="h-8 w-8 text-[#6366f1]" aria-hidden="true" />
              </div>
              <p className="mt-6 text-xl font-semibold text-slate-950">Drag and drop your image here</p>
              <p className="mt-2 text-sm text-slate-500">or click to browse</p>
            </>
          )}
        </div>

        {error ? <p className="mt-4 text-sm font-medium text-red-600">{error}</p> : null}

        <button
          type="button"
          onClick={() => void handleDigitize()}
          disabled={!file || isUploading}
          className="mt-8 inline-flex h-12 min-w-40 items-center justify-center rounded-md bg-[#6366f1] px-6 text-base font-semibold text-white shadow-sm hover:bg-[#5558e6] disabled:cursor-not-allowed disabled:bg-slate-300"
        >
          {isUploading ? (
            <>
              <Loader2 className="mr-2 h-5 w-5 animate-spin" aria-hidden="true" />
              Uploading
            </>
          ) : (
            "Digitize Now"
          )}
        </button>
      </div>
    </div>
  );
}
