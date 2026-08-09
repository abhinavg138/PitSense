import axios from "axios";

const API = axios.create({
    baseURL: "http://127.0.0.1:8000",
});

export const fetchSimulationSamples = async () => {
    const res = await API.get("/simulation/samples");
    return res.data;
};

export const fetchSimulationAudioBlob = async (filename) => {
    const res = await API.get(`/simulation/audio/${filename}`, {
        responseType: "blob",
    });
    return res.data;
};

export const resetBackendSession = async (sessionId = "simulation_session") => {
    const res = await API.post(`/session/reset?session_id=${sessionId}`);
    return res.data;
};

export default API;