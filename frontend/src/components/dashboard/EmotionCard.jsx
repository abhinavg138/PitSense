export default function EmotionCard() {
    return (
        <div className="bg-[#181D28] rounded-2xl border border-[#2A3342] p-6">

            <h2 className="text-xl font-semibold mb-5">
                Driver Status
            </h2>

            <div className="space-y-5">

                <div>
                    <p>Stress</p>
                    <progress className="w-full" value="0" max="100"></progress>
                </div>

                <div>
                    <p>Fatigue</p>
                    <progress className="w-full" value="0" max="100"></progress>
                </div>

                <div>
                    <p>Confidence</p>
                    <progress className="w-full" value="0" max="100"></progress>
                </div>

            </div>

        </div>
    );
}