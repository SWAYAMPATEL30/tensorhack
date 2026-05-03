import VideoOnboarding from "@/components/VideoOnboarding";

export const metadata = {
  title: "Poonawalla Fincorp Loan Wizard",
  description: "Video-Based Digital Loan Origination & Risk Assessment System",
};

export default function Home() {
  return (
    <main className="min-h-screen bg-gray-50 flex flex-col items-center justify-start py-10 px-4">
      <div className="w-full max-w-6xl mb-8">
        <h1 className="text-3xl font-extrabold text-gray-900 tracking-tight">
          Poonawalla Fincorp{" "}
          <span className="text-indigo-600">Loan Wizard</span>
        </h1>
        <p className="mt-1.5 text-base text-gray-500">
          Video-Based Digital Loan Origination &amp; Risk Assessment System
        </p>
      </div>
      <VideoOnboarding />
    </main>
  );
}
