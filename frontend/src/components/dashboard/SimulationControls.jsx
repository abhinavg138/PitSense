import React from "react";
import { Play, Pause, SkipForward, RotateCcw, Radio, Sliders } from "lucide-react";

export default function SimulationControls({
    mode,
    setMode,
    simulationState,
    onStart,
    onPause,
    onNext,
    onReset,
    delaySeconds,
    setDelaySeconds,
    currentIndex,
    totalSamples,
    currentSample,
    isProcessing,
}) {
    return (
        <div
            className="rounded-3xl p-6 mb-8 animate-fade-in-up"
            style={{
                background: "rgba(255, 255, 255, 0.04)",
                backdropFilter: "blur(24px)",
                WebkitBackdropFilter: "blur(24px)",
                border: "1px solid rgba(255, 255, 255, 0.06)",
                boxShadow: "0 4px 20px rgba(0,0,0,0.3)",
            }}
        >
            <div className="flex items-center justify-between flex-wrap gap-4 pb-4 mb-4 border-b border-white/5">
                <div className="flex items-center gap-3">
                    <div
                        className="w-10 h-10 rounded-2xl flex items-center justify-center"
                        style={{ background: "rgba(10,132,255,0.12)", border: "1px solid rgba(10,132,255,0.25)" }}
                    >
                        <Radio size={18} className="text-blue-400" />
                    </div>
                    <div>
                        <h2 className="text-lg font-bold text-white tracking-tight">
                            Race Operation Mode
                        </h2>
                        <p className="text-[11px] text-zinc-400">
                            Switch between Manual Audio Upload and Dynamic Race Simulation Replay
                        </p>
                    </div>
                </div>

                {/* Mode Selector */}
                <div className="flex items-center gap-1 p-1 rounded-2xl bg-zinc-900/80 border border-white/5">
                    <button
                        type="button"
                        onClick={() => setMode("manual")}
                        className={`px-4 py-2 rounded-xl text-xs font-bold transition-all ${
                            mode === "manual"
                                ? "bg-blue-600 text-white shadow-lg"
                                : "text-zinc-400 hover:text-white hover:bg-white/5"
                        }`}
                    >
                        Manual Upload
                    </button>
                    <button
                        type="button"
                        onClick={() => setMode("simulation")}
                        className={`px-4 py-2 rounded-xl text-xs font-bold transition-all ${
                            mode === "simulation"
                                ? "bg-blue-600 text-white shadow-lg"
                                : "text-zinc-400 hover:text-white hover:bg-white/5"
                        }`}
                    >
                        ▶ Race Simulation Mode
                    </button>
                </div>
            </div>

            {mode === "simulation" && (
                <div className="space-y-4">
                    {/* Controls & Delay Selector */}
                    <div className="flex items-center justify-between flex-wrap gap-4">
                        <div className="flex items-center gap-2">
                            {simulationState === "running" ? (
                                <button
                                    type="button"
                                    onClick={onPause}
                                    className="flex items-center gap-2 px-5 py-2.5 rounded-2xl font-extrabold text-xs uppercase tracking-wider text-black bg-amber-400 hover:bg-amber-300 transition-all shadow-md active:scale-95"
                                >
                                    <Pause size={14} /> Pause
                                </button>
                            ) : (
                                <button
                                    type="button"
                                    onClick={onStart}
                                    className="flex items-center gap-2 px-5 py-2.5 rounded-2xl font-extrabold text-xs uppercase tracking-wider text-white bg-blue-600 hover:bg-blue-500 transition-all shadow-md active:scale-95"
                                >
                                    <Play size={14} /> {simulationState === "paused" ? "Resume" : "Start Simulation"}
                                </button>
                            )}

                            <button
                                type="button"
                                onClick={onNext}
                                disabled={isProcessing || currentIndex >= totalSamples - 1}
                                className="flex items-center gap-2 px-4 py-2.5 rounded-2xl font-bold text-xs uppercase tracking-wider text-zinc-200 bg-zinc-800 hover:bg-zinc-700 disabled:opacity-40 disabled:cursor-not-allowed transition-all border border-white/5"
                            >
                                <SkipForward size={14} /> Next Sample
                            </button>

                            <button
                                type="button"
                                onClick={onReset}
                                className="flex items-center gap-2 px-4 py-2.5 rounded-2xl font-bold text-xs uppercase tracking-wider text-zinc-400 hover:text-white bg-zinc-900/60 hover:bg-zinc-800 transition-all border border-white/5"
                            >
                                <RotateCcw size={14} /> Reset Session
                            </button>
                        </div>

                        {/* Delay Config */}
                        <div className="flex items-center gap-2 text-xs text-zinc-400 bg-zinc-900/60 px-3.5 py-2 rounded-2xl border border-white/5">
                            <Sliders size={13} className="text-zinc-400" />
                            <span className="font-medium">Playback Interval:</span>
                            <select
                                value={delaySeconds}
                                onChange={(e) => setDelaySeconds(Number(e.target.value))}
                                className="bg-zinc-800 text-white font-bold rounded-lg px-2.5 py-1 border border-white/10 focus:outline-none focus:border-blue-500"
                            >
                                <option value={1}>1 second</option>
                                <option value={2}>2 seconds (Default)</option>
                                <option value={3}>3 seconds</option>
                                <option value={5}>5 seconds</option>
                            </select>
                        </div>
                    </div>

                    {/* Progress Bar & Status */}
                    {totalSamples > 0 && (
                        <div className="p-4 rounded-2xl bg-zinc-900/40 border border-white/5 space-y-2">
                            <div className="flex items-center justify-between text-xs">
                                <span className="font-semibold text-zinc-300">
                                    {currentSample ? (
                                        <>
                                            Observation {currentIndex + 1} of {totalSamples} —{" "}
                                            <span className="text-white font-bold">
                                                {currentSample.driver_name || "Driver"} ({currentSample.team_name || "F1 Team"})
                                            </span>{" "}
                                            • Lap {currentSample.lap || "?"}
                                        </>
                                    ) : (
                                        "Simulation Ready"
                                    )}
                                </span>
                                <span className="text-[11px] font-extrabold uppercase px-2.5 py-0.5 rounded-full bg-blue-500/10 border border-blue-500/20 text-blue-400">
                                    {isProcessing
                                        ? `ANALYZING LAP ${currentSample?.lap || "?"}...`
                                        : simulationState === "running"
                                        ? "PLAYBACK ACTIVE"
                                        : simulationState === "paused"
                                        ? "PAUSED"
                                        : simulationState === "completed"
                                        ? "SIMULATION COMPLETE"
                                        : "READY"}
                                </span>
                            </div>

                            {/* Progress bar */}
                            <div className="w-full bg-zinc-800 rounded-full h-1.5 overflow-hidden">
                                <div
                                    className="bg-blue-500 h-full transition-all duration-300 rounded-full"
                                    style={{
                                        width: `${Math.min(100, ((currentIndex + 1) / totalSamples) * 100)}%`,
                                    }}
                                />
                            </div>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}
