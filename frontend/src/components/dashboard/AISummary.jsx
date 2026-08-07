export default function AISummary({ analysis }) {

    if (!analysis) {
        return (
            <div className="bg-[#181D28] border border-[#2A3342] rounded-2xl p-6">
                <h2 className="text-2xl font-bold">AI Race Engineer</h2>

                <p className="text-gray-400 mt-4">
                    Waiting for analysis...
                </p>
            </div>
        );
    }

    const driver = analysis.driver_analysis;

    return (
        <div className="bg-[#181D28] border border-[#2A3342] rounded-2xl p-6">

            <h2 className="text-2xl font-bold mb-5">
                AI Race Engineer
            </h2>

            <div className="space-y-5">

                <div>
                    <h3 className="font-semibold text-red-400">
                        Detected Issues
                    </h3>

                    <ul className="list-disc ml-6 mt-2">
                        {driver.issues.map((issue, index) => (
                            <li key={index}>
                                {issue}
                            </li>
                        ))}
                    </ul>
                </div>

                <div>
                    <h3 className="font-semibold text-green-400">
                        Recommendations
                    </h3>

                    <ul className="list-disc ml-6 mt-2">
                        {driver.recommendations.map((rec, index) => (
                            <li key={index}>
                                {rec}
                            </li>
                        ))}
                    </ul>
                </div>

            </div>

        </div>
    );
}