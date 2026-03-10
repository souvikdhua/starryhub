import express from 'express';
import axios from 'axios';

const router = express.Router();

// Get current weather for a location using Open-Meteo (No API Key Required)
router.get('/current', async (req, res) => {
    try {
        const { lat, lon } = req.query;
        if (!lat || !lon) return res.status(400).json({ error: 'Lat and lon required' });

        const url = `https://api.open-meteo.com/v1/forecast?latitude=${lat}&longitude=${lon}&current_weather=true`;
        const response = await axios.get(url);

        // Open-meteo weathercodes: 0 is clear, 1-3 is cloudy, etc.
        const code = response.data.current_weather.weathercode;
        let cond = "Clear";
        if (code > 0 && code <= 3) cond = "Cloudy";
        if (code >= 45 && code <= 48) cond = "Foggy";
        if (code >= 51 && code <= 67) cond = "Rain";
        if (code >= 71) cond = "Snow";

        res.json({
            temp: response.data.current_weather.temperature,
            condition: cond,
            visibility: 10000 // default mock
        });
    } catch (error) {
        console.error('Weather error:', error.message);
        res.status(500).json({ error: 'Failed to fetch weather data' });
    }
});

export default router;
