export default function EmotionCard({ analysis }) {

    if (!analysis) {
        return (
            <div className="bg-[#181D28] border border-[#2A3342] rounded-2xl p-6">
                <h2 className="text-2xl font-bold">Driver Status</h2>

                <p className="text-gray-400 mt-4">
                    Upload an audio file to begin analysis.
                </p>
            </div>
        );
    }

    const emotion = analysis.emotion;
    const driver = analysis.driver_analysis;

    return (
        <div className="bg-[#181D28] border border-[#2A3342] rounded-2xl p-6">

            <h2 className="text-2xl font-bold mb-5">
                Driver Status
            </h2>

            <div className="space-y-4">

                <div>
                    <p className="text-gray-400">Emotion</p>
                    <h3 className="text-xl font-semibold capitalize">
                        {emotion.emotion}
                    </h3>
                </div>

                <div>
                    <p className="text-gray-400">Driver State</p>
                    <h3 className="text-xl font-semibold">
                        {driver.driver_state}
                    </h3>
                </div>

                <div>
                    <p className="text-gray-400">
                        Confidence ({emotion.confidence}%)
                    </p>

                    <progress
                        className="w-full"
                        value={emotion.confidence}
                        max="100"
                    />
                </div>

                <div>
                    <p className="text-gray-400">
                        Stress ({driver.stress}%)
                    </p>

                    <progress
                        className="w-full"
                        value={driver.stress}
                        max="100"
                    />
                </div>

                <div>
                    <p className="text-gray-400">
                        Urgency ({driver.urgency}%)
                    </p>

                    <progress
                        className="w-full"
                        value={driver.urgency}
                        max="100"
                    />
                </div>

            </div>

        </div>
    );
}