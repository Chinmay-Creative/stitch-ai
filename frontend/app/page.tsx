import { Bot, Download, MessageSquareText, ScanLine } from "lucide-react";
import Link from "next/link";

const steps = [
  "Upload your image",
  "AI removes background and detects regions",
  "Stitch logic assigns thread paths",
  "Download DST or PES file",
];

const features = [
  {
    icon: Bot,
    title: "AI-Powered",
    description: "Computer vision detects every region automatically",
  },
  {
    icon: Download,
    title: "Real Machine Files",
    description: "Download DST and PES files your machine can run",
  },
  {
    icon: MessageSquareText,
    title: "Plain English Feedback",
    description: "Describe problems, AI fixes and learns forever",
  },
];

export default function Home() {
  return (
    <div className="bg-white">
      <section className="mx-auto flex min-h-[calc(100vh-4rem)] max-w-7xl flex-col items-center justify-center px-4 py-20 text-center sm:px-6 lg:px-8">
        <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-indigo-100 bg-indigo-50 px-4 py-2 text-sm font-medium text-[#6366f1]">
          <ScanLine className="h-4 w-4" aria-hidden="true" />
          AI embroidery digitizing
        </div>
        <h1 className="max-w-5xl text-4xl font-bold tracking-tight text-slate-950 sm:text-6xl lg:text-7xl">
          Turn any image into embroidery-ready files
        </h1>
        <p className="mt-6 max-w-2xl text-lg leading-8 text-slate-600 sm:text-xl">
          AI-powered digitizing in seconds. No skills needed. Free to try.
        </p>
        <div className="mt-10 flex flex-col gap-3 sm:flex-row">
          <Link
            href="/upload"
            className="inline-flex h-12 items-center justify-center rounded-md bg-[#6366f1] px-6 text-base font-semibold text-white shadow-sm hover:bg-[#5558e6]"
          >
            Start Digitizing Free
          </Link>
          <Link
            href="#how-it-works"
            className="inline-flex h-12 items-center justify-center rounded-md border border-slate-300 bg-white px-6 text-base font-semibold text-slate-800 hover:border-[#6366f1] hover:text-[#6366f1]"
          >
            See how it works
          </Link>
        </div>
      </section>

      <section id="how-it-works" className="border-y border-slate-200 bg-white px-4 py-16 sm:px-6 lg:px-8">
        <div className="mx-auto max-w-7xl">
          <h2 className="text-center text-3xl font-bold text-slate-950">How it works</h2>
          <div className="mt-10 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {steps.map((step, index) => (
              <div key={step} className="rounded-lg border border-slate-200 bg-white p-6">
                <div className="flex h-10 w-10 items-center justify-center rounded-full bg-indigo-50 text-sm font-bold text-[#6366f1]">
                  {index + 1}
                </div>
                <p className="mt-5 text-base font-semibold text-slate-900">{step}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="px-4 py-16 sm:px-6 lg:px-8">
        <div className="mx-auto grid max-w-7xl gap-5 md:grid-cols-3">
          {features.map((feature) => {
            const Icon = feature.icon;
            return (
              <article key={feature.title} className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
                <Icon className="h-7 w-7 text-[#6366f1]" aria-hidden="true" />
                <h3 className="mt-5 text-xl font-bold text-slate-950">{feature.title}</h3>
                <p className="mt-3 leading-7 text-slate-600">{feature.description}</p>
              </article>
            );
          })}
        </div>
      </section>

      <footer className="border-t border-slate-200 px-4 py-8 text-center text-sm text-slate-500">
        StitchAI 2026 — Built at OpenAI x Outskill Hackathon
      </footer>
    </div>
  );
}
