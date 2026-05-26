"use client";

import { useEffect, useState } from "react";
import { CheckCircle2, Download, Image, Loader2, Search } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { pollStatus } from "@/lib/api";

const steps = [
  { label: "Removing background", icon: Image },
  { label: "Detecting stitch regions", icon: Search },
  { label: "Generating stitch file", icon: Download },
];

function getStepFromStatus(status: string) {
  if (["starting", "removing_bg", "enhancing"].includes(status)) {
    return 0;
  }

  if (["vectorizing", "analyzing", "classifying"].includes(status)) {
    return 1;
  }

  if (["optimizing", "complete"].includes(status)) {
    return 2;
  }

  return 0;
}

function getFriendlyStatus(status: string) {
  const labels: Record<string, string> = {
    starting: "Preparing your design",
    removing_bg: "Removing background",
    enhancing: "Enhancing image clarity",
    vectorizing: "Tracing stitch regions",
    analyzing: "Analyzing shapes and colors",
    classifying: "Choosing stitch types",
    optimizing: "Optimizing stitch file",
    complete: "Complete",
  };

  return labels[status] ?? "Processing with StitchAI";
}

export default function ProcessingPage() {
  const router = useRouter();
  const [activeStep, setActiveStep] = useState(0);
  const [statusText, setStatusText] = useState("Preparing your design");
  const [error, setError] = useState("");
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    const jobId = sessionStorage.getItem("job_id");

    if (!jobId) {
      window.setTimeout(() => setError("We could not find an active upload. Please start again."), 0);
      return;
    }

    let cancelled = false;

    pollStatus(jobId, (status) => {
      setActiveStep(getStepFromStatus(status));
      setStatusText(getFriendlyStatus(status));
    }).then((finalStatus) => {
      if (cancelled) {
        return;
      }

      if (finalStatus === "complete") {
        router.push("/result");
      } else {
        setError("Something went wrong while processing your design. Please try again.");
      }
    });

    return () => {
      cancelled = true;
    };
  }, [router]);

  return (
    <div className="flex min-h-[calc(100vh-4rem)] items-center justify-center bg-white px-4 py-12 sm:px-6 lg:px-8">
      {!mounted ? null : (
      <div className="w-full max-w-4xl text-center">
        <h1 className="text-4xl font-bold tracking-tight text-slate-950">Processing your design</h1>
        <p className="mt-4 text-lg text-slate-600">This takes about 30 seconds</p>

        {error ? (
          <div className="mx-auto mt-10 max-w-xl rounded-lg border border-red-200 bg-red-50 p-6">
            <p className="font-medium text-red-700">{error}</p>
            <Link
              href="/upload"
              className="mt-5 inline-flex h-11 items-center justify-center rounded-md bg-[#6366f1] px-5 text-sm font-semibold text-white hover:bg-[#5558e6]"
            >
              Try again
            </Link>
          </div>
        ) : (
          <>
            <div className="mt-12 grid gap-4 md:grid-cols-3">
              {steps.map((step, index) => {
                const Icon = step.icon;
                const isCompleted = index < activeStep;
                const isActive = index === activeStep;

                return (
                  <div
                    key={step.label}
                    className={`rounded-xl border p-6 text-left transition ${
                      isActive
                        ? "border-[#6366f1] bg-indigo-50"
                        : isCompleted
                          ? "border-green-200 bg-green-50"
                          : "border-slate-200 bg-white"
                    }`}
                  >
                    <div
                      className={`flex h-12 w-12 items-center justify-center rounded-full ${
                        isCompleted ? "bg-green-100 text-green-600" : isActive ? "bg-white text-[#6366f1]" : "bg-slate-100 text-slate-500"
                      }`}
                    >
                      {isCompleted ? <CheckCircle2 className="h-6 w-6" /> : <Icon className="h-6 w-6" />}
                    </div>
                    <p className="mt-5 font-semibold text-slate-950">{step.label}</p>
                  </div>
                );
              })}
            </div>

            <div className="mt-10 overflow-hidden rounded-full bg-slate-100">
              <div
                className="h-3 rounded-full bg-[#6366f1] transition-all duration-700"
                style={{ width: `${Math.max(20, ((activeStep + 1) / steps.length) * 100)}%` }}
              />
            </div>
            <div className="mt-6 flex items-center justify-center gap-2 text-sm font-medium text-slate-500">
              <Loader2 className="h-4 w-4 animate-spin text-[#6366f1]" aria-hidden="true" />
              {statusText}
            </div>
          </>
        )}
      </div>
      )}
    </div>
  );
}
