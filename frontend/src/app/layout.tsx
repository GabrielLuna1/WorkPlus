import type { Metadata } from "next";
import { Poppins, Inter, Geist_Mono } from "next/font/google";
import { Toaster } from "sonner";
import Sidebar from "@/components/layout/Sidebar";
import { ChatPanel } from "@/components/chat/ChatPanel";
import { ChatProvider } from "@/lib/chat-context";
import "./globals.css";

const poppins = Poppins({
  weight: ["400", "500", "600", "700"],
  variable: "--font-poppins",
  subsets: ["latin"],
});

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "WorkHunter | Platform",
  description: "Plataforma avançada de monitoramento e análise de vagas.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="pt-BR" className={`${poppins.variable} ${inter.variable} ${geistMono.variable} h-full antialiased dark`}>
      <body className="min-h-full bg-canvas text-ink">
        <ChatProvider>
          <div className="flex h-screen overflow-hidden bg-canvas">
            <Sidebar />
            <main className="flex-1 ml-[280px] overflow-y-auto relative z-[1]">
              {children}
            </main>
          </div>
          <ChatPanel />
          <Toaster
            position="bottom-right"
            richColors
            closeButton
            toastOptions={{
              duration: 5000,
            }}
          />
        </ChatProvider>
      </body>
    </html>
  );
}
