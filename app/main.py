#!/usr/bin/env python3
from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse, JSONResponse
import httpx
import os
import sys
import time
import uvicorn

# check if ICECAST_RELAYS env exists
if not os.getenv("ICECAST_RELAYS"):
    print("Please set the ICECAST_RELAYS environment variable!")
    print("ICECAST_RELAYS='server1.example.com,server2.example.com'")
    sys.exit(1)

# split icecast servers, trim whitespace, filter empty entries
ICECAST_RELAYS = [s.strip() for s in os.environ['ICECAST_RELAYS'].split(",") if s.strip()]

if not ICECAST_RELAYS:
    print("ICECAST_RELAYS contains no valid server entries!")
    sys.exit(1)

PORT = int(os.getenv("PORT", "8080"))
ICECAST_RELAY_SCHEME = os.getenv("ICECAST_RELAY_SCHEME", "http")
CACHE_TTL = int(os.getenv("CACHE_TTL", "60"))

print("icecast-balancer starts with following servers ...")
print(ICECAST_RELAYS)

_cache = {}
_cache_time = 0.0


async def get_listeners_from_icecast_servers():
    global _cache, _cache_time

    if CACHE_TTL > 0 and _cache and (time.monotonic() - _cache_time) < CACHE_TTL:
        return _cache

    server_listeners = {}

    async with httpx.AsyncClient(timeout=5) as client:
        for server in ICECAST_RELAYS:
            try:
                r = await client.get(f"{ICECAST_RELAY_SCHEME}://{server}/status-json.xsl")
                r.raise_for_status()
            except (httpx.RequestError, httpx.HTTPStatusError):
                # if icecastserver is not reachable continue with next icecastserver
                continue

            # iterate over json-status.xsl from icecastserver and sum listeners from all mountpoints
            data = r.json()
            if "source" in data["icestats"]:
                listeners = data["icestats"]["source"]
                listeners_sum = []
                if isinstance(listeners, list):
                    for source in listeners:
                        listeners_sum.append(source["listeners"])

                if isinstance(listeners, dict):
                    listeners_sum.append(listeners["listeners"])

                server_listeners[server] = sum(listeners_sum)

    sorted_server_listeners = dict(sorted(
        server_listeners.items(), key=lambda item: item[1]))

    if CACHE_TTL > 0 and sorted_server_listeners:
        _cache = sorted_server_listeners
        _cache_time = time.monotonic()

    return sorted_server_listeners


# set fastapi app
app = FastAPI()


# status route
@app.get('/status')
async def icecast_status():

    listeners = await get_listeners_from_icecast_servers()

    if not listeners:
        return JSONResponse({"message": "No icecast relay is reachable!"}, status_code=400)

    return listeners


# balancer route
@app.get('/{path:path}')
async def icecast_redirector(path: str, request: Request):
    if not path:
        return JSONResponse({"message": "Please give me a stream path!"}, status_code=400)

    scheme = "http"

    if 'x-forwarded-proto' in request.headers:
        scheme = request.headers["x-forwarded-proto"]

    if request.url.scheme == "https":
        scheme = "https"

    listeners = await get_listeners_from_icecast_servers()

    if not listeners:
        return JSONResponse({"message": "No icecast relay is reachable!"}, status_code=400)

    server = next(iter(listeners))
    return RedirectResponse(f"{scheme}://{server}/{path}")


if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=PORT)
