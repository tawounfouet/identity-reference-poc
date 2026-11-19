import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Identity Reference POC",
  description: "Django allauth Headless + Next.js reference implementation",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="fr">
      <body>{children}</body>
    </html>
  );
}
