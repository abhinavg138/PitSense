export function asNumber(value) {
    if (value === null || value === undefined || value === "") return null;
    const numeric = Number(value);
    return Number.isFinite(numeric) ? numeric : null;
}

export function formatNumber(value, decimals = 3) {
    const numeric = asNumber(value);
    return numeric === null ? null : numeric.toFixed(decimals);
}

export function normalizeTelemetryPoint(point = {}, fallbackIndex = 0) {
    const lap = asNumber(point.lap);
    const lapTime = asNumber(point.lap_time ?? point.lap_time_seconds);
    const stress = asNumber(point.stress ?? point.stress_index);
    const available = point.available === true || lap !== null || lapTime !== null;

    return {
        index: asNumber(point.index) ?? fallbackIndex + 1,
        timestamp: point.timestamp || null,
        filename: point.filename || point.audio_file || null,
        available,
        status: point.status || (available ? "PARTIAL" : "UNAVAILABLE"),
        lap,
        lap_time: lapTime,
        stress,
        sector_1: asNumber(point.sector_1),
        sector_2: asNumber(point.sector_2),
        sector_3: asNumber(point.sector_3),
        i1_speed: asNumber(point.i1_speed),
        i2_speed: asNumber(point.i2_speed),
        top_speed: asNumber(point.top_speed),
    };
}

export function normalizeTelemetrySeries(analysis) {
    const rawSeries = analysis?.telemetry_series;
    const rawPoints = Array.isArray(rawSeries?.points) ? rawSeries.points : [];
    let points = rawPoints.map((point, index) => normalizeTelemetryPoint(point, index));

    if (points.length === 0 && analysis?.telemetry) {
        points = [normalizeTelemetryPoint({
            ...analysis.telemetry,
            filename: analysis.filename || analysis.telemetry.audio_file,
            stress: analysis?.stress_index?.stress_index ?? analysis?.driver_analysis?.stress,
        })];
    }

    const usablePoints = points.filter(point => point.available);
    let status = rawSeries?.status;
    if (!status) {
        if (usablePoints.length === 0) status = "UNAVAILABLE";
        else if (usablePoints.length < 2) status = "INSUFFICIENT";
        else status = usablePoints.some(point => point.status === "AVAILABLE") ? "AVAILABLE" : "PARTIAL";
    }

    return {
        available: usablePoints.length > 0,
        status,
        sample_count: asNumber(rawSeries?.sample_count) ?? points.length,
        point_count: asNumber(rawSeries?.point_count) ?? usablePoints.length,
        points,
        usablePoints,
    };
}

export function getCurrentTelemetry(analysis) {
    const telemetry = analysis?.telemetry || {};
    const current = normalizeTelemetryPoint({
        ...telemetry,
        filename: analysis?.filename || telemetry.audio_file,
        stress: analysis?.stress_index?.stress_index ?? analysis?.driver_analysis?.stress,
    });

    return {
        ...current,
        audio_file: telemetry.audio_file || analysis?.filename || current.filename,
        radio_time: telemetry.radio_time || null,
        is_pit_out_lap: telemetry.is_pit_out_lap ?? null,
    };
}
