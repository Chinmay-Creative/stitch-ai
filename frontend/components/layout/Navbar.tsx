import { Scissors } from "lucide-react";
import Link from "next/link";

export default function Navbar() {
  return (
    <header className="sticky top-0 z-50 w-full border-b border-slate-200 bg-white/95 backdrop-blur">
      <nav className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
        <Link href="/" className="flex items-center gap-2 text-slate-950">
          <Scissors className="h-6 w-6 text-[#6366f1]" aria-hidden="true" />
          <span className="text-lg font-semibold">StitchAI</span>
        </Link>

        <div className="flex items-center gap-3 sm:gap-6">
          <Link
            href="/#how-it-works"
            className="hidden text-sm font-medium text-slate-600 hover:text-slate-950 sm:inline"
          >
            How it works
          </Link>
          <Link
            href="/upload"
            className="inline-flex h-10 items-center justify-center rounded-md bg-[#6366f1] px-4 text-sm font-semibold text-white shadow-sm hover:bg-[#5558e6]"
          >
            Start Free
          </Link>
        </div>
      </nav>
    </header>
  );
}
