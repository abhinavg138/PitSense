import { Home, Mic, FolderOpen, FileText, Settings } from "lucide-react";

export default function Sidebar() {
    return (
        <aside className="w-64 bg-[#11151D] border-r border-[#252B36] p-6">

            <h2 className="text-2xl font-bold text-blue-500">
                PitSense AI
            </h2>

            <p className="text-gray-500 text-sm mt-1">
                v1.0 Prototype
            </p>

            <nav className="mt-10 space-y-4">

                <button className="flex items-center gap-3 w-full text-left p-3 rounded-xl hover:bg-[#1A202C]">
                    <Home size={20} />
                    Dashboard
                </button>

                <button className="flex items-center gap-3 w-full text-left p-3 rounded-xl hover:bg-[#1A202C]">
                    <Mic size={20} />
                    Analyze Audio
                </button>

                <button className="flex items-center gap-3 w-full text-left p-3 rounded-xl hover:bg-[#1A202C]">
                    <FolderOpen size={20} />
                    Sessions
                </button>

                <button className="flex items-center gap-3 w-full text-left p-3 rounded-xl hover:bg-[#1A202C]">
                    <FileText size={20} />
                    Reports
                </button>

                <button className="flex items-center gap-3 w-full text-left p-3 rounded-xl hover:bg-[#1A202C]">
                    <Settings size={20} />
                    Settings
                </button>

            </nav>

        </aside>
    );
}