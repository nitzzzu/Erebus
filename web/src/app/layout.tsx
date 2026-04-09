import type { Metadata } from "next";
import "./globals.css";
import { Sidebar } from "@/components/sidebar";
import { ChatProvider } from "@/store/chat-context";

export const metadata: Metadata = {
  title: "Erebus — AI Agent",
  description: "Feature-packed AI agent powered by Agno",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="h-full antialiased dark">
      <body className="flex h-screen overflow-hidden font-sans">
        <ChatProvider>
          <Sidebar />
          <main className="flex-1 overflow-y-auto pt-14 md:pt-0">
            {children}
          </main>
        </ChatProvider>
      </body>
    </html>
  );
}
