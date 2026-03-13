export default {
    async fetch(request, env, ctx) {
        const spaceUrl = "https://theskyturnsgray1-starrygate.hf.space";
        const url = new URL(request.url);

        // Rewrite the target URL to point to the HF Space
        const targetUrl = new URL(url.pathname + url.search, spaceUrl);

        // Create new request with the target URL while keeping original headers/method
        const newRequest = new Request(targetUrl, request);
        newRequest.headers.set('Host', new URL(spaceUrl).hostname);

        return fetch(newRequest);
    },
};
