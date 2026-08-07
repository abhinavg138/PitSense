import { useRef, useState } from "react";
import { UploadCloud, Music2 } from "lucide-react";
import API from "../../services/api";

export default function UploadCard({ setAnalysis }) {

    const fileInputRef = useRef(null);

    const [audioFile, setAudioFile] = useState(null);
    const [audioURL, setAudioURL] = useState(null);
    const [uploading, setUploading] = useState(false);

    const [transcript, setTranscript] = useState("");

    async function handleFile(file) {

        if (!file) return;

        setAudioFile(file);

        setAudioURL(URL.createObjectURL(file));

        const formData = new FormData();

        formData.append("file", file);

        try {

            setUploading(true);

            const response = await API.post(
                "/upload",
                formData
            );

            console.log(response.data);

            setAnalysis(response.data);

            setTranscript(response.data.transcript);

            alert("Upload Successful 🚀");

        }

        catch (err) {

            console.error(err);

            alert("Upload Failed");

        }

        finally {

            setUploading(false);

        }

    }

    return (

        <div className="bg-[#181D28] border border-[#2A3342] rounded-2xl p-8">

            <input
                type="file"
                hidden
                accept="audio/*"
                ref={fileInputRef}
                onChange={(e) => handleFile(e.target.files[0])}
            />

            {!audioFile ? (

                <div className="text-center">

                    <UploadCloud
                        size={60}
                        className="mx-auto text-blue-500"
                    />

                    <h2 className="text-3xl font-bold mt-5">
                        Upload Race Radio
                    </h2>

                    <p className="text-gray-400 mt-2">
                        MP3 • WAV • M4A
                    </p>

                    <button
                        onClick={() => fileInputRef.current.click()}
                        className="mt-6 bg-blue-600 hover:bg-blue-700 px-7 py-3 rounded-xl"
                    >
                        Browse Files
                    </button>

                </div>

            ) : (

                <div>

                    <div className="flex items-center gap-3">

                        <Music2 className="text-blue-500" />

                        <div>

                            <h3 className="font-semibold">
                                {audioFile.name}
                            </h3>

                            <p className="text-gray-400 text-sm">
                                {(audioFile.size / 1024 / 1024).toFixed(2)} MB
                            </p>

                        </div>

                    </div>

                    <audio
                        controls
                        src={audioURL}
                        className="w-full mt-5"
                    />

                    <div className="mt-6 bg-[#11151D] p-5 rounded-xl border border-[#2A3342]">

                        <h3 className="font-semibold mb-3">
                            Whisper Transcript
                        </h3>

                        <p className="text-gray-300 whitespace-pre-wrap">

                            {
                                transcript
                                    ? transcript
                                    : "Waiting..."

                            }

                        </p>

                    </div>

                    <button
                        disabled={uploading}
                        className="mt-5 bg-green-600 px-5 py-2 rounded-xl"
                    >
                        {
                            uploading
                                ? "Uploading..."
                                : "Uploaded"
                        }
                    </button>

                </div>

            )}

        </div>

    );

}