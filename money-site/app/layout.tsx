import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "MONEY Ω",
  description: "Un solo sistema para descubrir recursos, revisar mercados y registrar ingresos y gastos con evidencia. Sin ejecución financiera.",
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
