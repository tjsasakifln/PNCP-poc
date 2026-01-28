import type { Metadata } from "next";
import "./globals.css";
import { ThemeProvider } from "./components/ThemeProvider";

export const metadata: Metadata = {
  title: "BidIQ Uniformes",
  description: "Busca inteligente de licitações no PNCP",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="pt-BR" suppressHydrationWarning>
      <head>
        <script
          dangerouslySetInnerHTML={{
            __html: `
              try {
                const theme = localStorage.getItem('bidiq-theme');
                if (theme === 'dark' || theme === 'dim') {
                  document.documentElement.classList.add('dark');
                }
                if (theme === 'paperwhite') {
                  document.documentElement.style.setProperty('--background', '#F5F0E8');
                } else if (theme === 'sepia') {
                  document.documentElement.style.setProperty('--background', '#EDE0CC');
                } else if (theme === 'dim') {
                  document.documentElement.style.setProperty('--background', '#2A2A2E');
                  document.documentElement.style.setProperty('--foreground', '#e0e0e0');
                } else if (theme === 'dark') {
                  document.documentElement.style.setProperty('--background', '#121212');
                  document.documentElement.style.setProperty('--foreground', '#e0e0e0');
                }
              } catch(e) {}
            `,
          }}
        />
      </head>
      <body>
        <ThemeProvider>{children}</ThemeProvider>
      </body>
    </html>
  );
}
