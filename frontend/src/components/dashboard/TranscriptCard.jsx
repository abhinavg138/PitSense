export default function TranscriptCard({ analysis }) {

    if (!analysis) {
        return (
            <div className="bg-[#181D28] border border-[#2A3342] rounded-2xl p-6">

                <h2 className="text-2xl font-bold mb-4">
                    Transcript
                </h2>

                <p className="text-gray-400">
                    Waiting for uploaded race radio...
                </p>

            </div>
        );
    }

    return (

        <div className="bg-[#181D28] border border-[#2A3342] rounded-2xl p-6">

            <h2 className="text-2xl font-bold mb-4">
                Transcript
            </h2>

            <div className="bg-[#11151D] rounded-xl p-5">

                <p className="text-gray-300 whitespace-pre-wrap leading-7">
                    {analysis.transcript}
                </p>

            </div>

        </div>

    );

}