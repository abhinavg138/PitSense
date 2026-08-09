import test from "node:test";
import assert from "node:assert/strict";

import {
    getCurrentTelemetry,
    normalizeTelemetrySeries,
} from "./telemetry.js";

test("normalizes backend telemetry_series for chart rendering", () => {
    const analysis = {
        filename: "lap_33.mp3",
        telemetry: {
            available: true,
            lap: 33,
            lap_time: 97.449,
            audio_file: "lap_33.mp3",
        },
        telemetry_series: {
            available: true,
            status: "AVAILABLE",
            sample_count: 2,
            point_count: 2,
            points: [
                { index: 1, lap: 4, lap_time: 99.17, stress: 33, available: true, status: "PARTIAL" },
                { index: 2, lap: 33, lap_time: 97.449, stress: 48, available: true, status: "AVAILABLE" },
            ],
        },
    };

    const series = normalizeTelemetrySeries(analysis);

    assert.equal(series.available, true);
    assert.equal(series.status, "AVAILABLE");
    assert.equal(series.point_count, 2);
    assert.equal(series.usablePoints[0].lap, 4);
    assert.equal(series.usablePoints[1].lap_time, 97.449);
    assert.equal(series.usablePoints[1].stress, 48);
});

test("falls back to current telemetry when the series is missing", () => {
    const analysis = {
        filename: "lap_04.mp3",
        telemetry: {
            available: true,
            lap: "4",
            lap_time: "99.170",
            audio_file: "lap_04.mp3",
        },
        stress_index: { stress_index: 33 },
    };

    const current = getCurrentTelemetry(analysis);
    const series = normalizeTelemetrySeries(analysis);

    assert.equal(current.available, true);
    assert.equal(current.lap, 4);
    assert.equal(current.lap_time, 99.17);
    assert.equal(series.status, "INSUFFICIENT");
    assert.equal(series.usablePoints.length, 1);
});

test("keeps unavailable telemetry explicit", () => {
    const analysis = {
        filename: "custom_upload.mp3",
        telemetry: { available: false },
        telemetry_series: {
            available: false,
            status: "UNAVAILABLE",
            sample_count: 1,
            point_count: 0,
            points: [{ index: 1, filename: "custom_upload.mp3", available: false, status: "UNAVAILABLE" }],
        },
    };

    const current = getCurrentTelemetry(analysis);
    const series = normalizeTelemetrySeries(analysis);

    assert.equal(current.available, false);
    assert.equal(series.available, false);
    assert.equal(series.status, "UNAVAILABLE");
    assert.equal(series.usablePoints.length, 0);
});
