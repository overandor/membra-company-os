import type { Metadata } from "next";
import "@/styles/globals.css";
import { WalletContextProvider } from "@/components/wallet/WalletProvider";
import { Navbar } from "@/components/layout/Navbar";

export const metadata: Metadata = {
  title: "MEMBRA — Chat-to-Chain Human Value Infrastructure",
  description:
    "MEMBRA turns each chat into an executable terminal-backed protocol workspace where the LLM can build, test, hash, commit, and deploy to Solana devnet under policy.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-background text-text-primary antialiased">
        <WalletContextProvider>
          <Navbar />
          <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            {children}
          </main>
        </WalletContextProvider>
      </body>
    </html>
  );
}
