import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "MONEY Ω · Observatorio",
  description: "Observatorio privado de criptomonedas: estimaciones experimentales, mercados y trazabilidad. Sin ejecución financiera.",
  icons: {
    icon: "/favicon.svg",
    shortcut: "/favicon.svg",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="es">
      <body className="antialiased">{children}</body>
    </html>
  );
}
