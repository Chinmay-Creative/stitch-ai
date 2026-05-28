import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "StitchAI",
  description: "AI-powered embroidery digitizing in seconds",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="bg-white text-slate-900">
        <main>{children}</main>
      </body>
    </html>
  );
}
