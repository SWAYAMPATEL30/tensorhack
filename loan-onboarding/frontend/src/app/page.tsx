import VideoOnboarding from "@/components/VideoOnboarding";

export default function Home() {
  return (
    <main className="min-h-screen bg-gray-50 flex flex-col items-center justify-center p-4">
      <div className="w-full max-w-7xl mb-12 text-center pt-8">
        <h1 className="text-5xl font-extrabold text-gray-900 tracking-tight">
          Poonawalla Fincorp <span className="text-transparent bg-clip-text bg-gradient-to-r from-indigo-600 to-purple-600">Loan Wizard</span>
        </h1>
        <p className="mt-4 text-xl text-gray-600 max-w-2xl mx-auto">
          Agentic AI Video Call Based Onboarding System
        </p>
      </div>
      <VideoOnboarding />
    </main>
  );
}
