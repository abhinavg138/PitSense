import { UploadCloud } from "lucide-react";

export default function UploadCard() {
    return (
        <div className="bg-[#181D28] rounded-2xl border border-[#2A3342] p-10 text-center">

            <UploadCloud
                size={50}
                className="mx-auto text-blue-500"
            />

            <h2 className="text-2xl font-semibold mt-5">
                Upload Race Radio
            </h2>

            <p className="text-gray-400 mt-2">
                Drag & Drop MP3, WAV or M4A
            </p>

            <button className="mt-6 bg-blue-600 hover:bg-blue-700 transition px-6 py-3 rounded-xl">
                Browse Files
            </button>

        </div>
    );
}