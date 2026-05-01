import VideoOnboarding from "@/components/VideoOnboarding";

export default function Home() {
  return (
    <main className="min-h-screen bg-gray-50 flex flex-col items-center justify-center p-4">
      <div className="w-full max-w-6xl mb-8">
        <h1 className="text-4xl font-extrabold text-gray-900 tracking-tight">
          Poonawalla Fincorp <span className="text-indigo-600">Loan Wizard</span>
        </h1>
        <p className="mt-2 text-lg text-gray-600">
          Video-Based Digital Loan Origination & Risk Assessment System
        </p>
      </div>
      <VideoOnboarding />
    </main>
  );
}
