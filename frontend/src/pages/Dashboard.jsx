import Sidebar from "../components/common/Sidebar";
import UploadCard from "../components/upload/UploadCard";
import TranscriptCard from "../components/dashboard/TranscriptCard";
import EmotionCard from "../components/dashboard/EmotionCard";
import AISummary from "../components/dashboard/AISummary";

export default function Dashboard() {
  return (
    <div className="flex min-h-screen bg-[#090B10] text-white">

      <Sidebar />

      <main className="flex-1 p-8">

        <div className="mb-8">
          <h1 className="text-4xl font-bold">
            PitSense AI
          </h1>

          <p className="text-gray-400 mt-2">
            Driver Communication Intelligence Platform
          </p>
        </div>

        <div className="grid grid-cols-12 gap-6">

          <div className="col-span-12">
            <UploadCard />
          </div>

          <div className="col-span-8">
            <TranscriptCard />
          </div>

          <div className="col-span-4">
            <EmotionCard />
          </div>

          <div className="col-span-12">
            <AISummary />
          </div>

        </div>

      </main>

    </div>
  );
}