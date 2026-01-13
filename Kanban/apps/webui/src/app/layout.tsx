import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Monoco Kanban",
  description: "Task as Code Client",
  icons: {
    icon: "/logo.svg",
    shortcut: "/logo.svg",
    apple: "/logo.svg",
  },
};

import { Providers } from "./providers";
import LayoutShell from "./components/LayoutShell";
import { ThemeProvider } from "../components/theme-provider";

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={`${inter.className}`}>
        <ThemeProvider defaultTheme="system" storageKey="monoco-ui-theme">
          <Providers>
            <LayoutShell>{children}</LayoutShell>
          </Providers>
        </ThemeProvider>
      </body>
    </html>
  );
}
