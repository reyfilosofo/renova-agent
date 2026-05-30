import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  metadataBase: new URL(process.env.NEXT_PUBLIC_SITE_URL ?? "http://localhost:3000"),
  title: "RENOVA Agent — Rey Filósofo by SERESARTE",
  description:
    "A first technical interface for the ontological, existential and renewative framework of la ℛenova.",
  openGraph: {
    title: "RENOVA Agent",
    description:
      "AI interface for renewative philosophy, symbolic engineering and life-centered systems.",
    images: ["/assets/social-card.svg"]
  }
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
