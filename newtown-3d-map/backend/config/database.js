import { createClient } from 'redis';

let redisClient;

export const initRedis = async () => {
    try {
        redisClient = createClient({
            url: process.env.REDIS_URL || 'redis://localhost:6379'
        });

        redisClient.on('error', (err) => console.log('Redis Client Error', err));

        await redisClient.connect();
        console.log('[Redis] Connected successfully');
    } catch (e) {
        console.warn('[Redis] Failed to connect, running without cache (or using memory map)');
    }
};

export const getRedisClient = () => redisClient;
