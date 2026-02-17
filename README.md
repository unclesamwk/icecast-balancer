# icecast-balancer

A lightweight load balancer for Icecast relays. It redirects listeners to the relay with the fewest active connections, distributing the load evenly across all relays.

## Prerequisites

All configured Icecast relays must serve the same mountpoints. This is typically achieved with an [Icecast master-relay setup](https://www.icecast.org/docs/icecast-trunk/relaying/).

## How it works

1. A listener requests a stream, e.g. `http://balancer.example.com/live`
2. The balancer queries the `/status-json.xsl` endpoint of each configured relay
3. Listener counts are summed across all mountpoints per relay
4. The listener is redirected (HTTP 307) to the relay with the fewest listeners

Unreachable relays are automatically skipped.

## Configuration

| Environment Variable | Required | Default | Description |
|---|---|---|---|
| `ICECAST_RELAYS` | Yes | - | Comma-separated list of Icecast relay hostnames (without protocol) |
| `PORT` | No | `8080` | Port the balancer listens on |

## Quick Start

### Docker Run

```bash
docker run -d \
  -p 8080:8080 \
  -e ICECAST_RELAYS='relay1.example.com,relay2.example.com' \
  unclesamwk/icecast-balancer:latest
```

### Docker Compose

```yaml
services:
  icecast-balancer:
    build: .
    image: unclesamwk/icecast-balancer:latest
    ports:
      - 8080:8080
    environment:
      ICECAST_RELAYS: relay1.example.com,relay2.example.com
```

```bash
docker compose up -d
```

## API

### `GET /status`

Returns the current listener count for each reachable relay, sorted ascending.

```bash
curl http://localhost:8080/status
```

```json
{
  "relay2.example.com": 15,
  "relay1.example.com": 55
}
```

### `GET /<mountpoint>`

Redirects to the least-loaded relay for the given mountpoint.

```bash
curl -v http://localhost:8080/live
# < HTTP/1.1 307 Temporary Redirect
# < location: http://relay2.example.com/live
```

## Reverse Proxy

The balancer supports running behind a reverse proxy (e.g. Traefik, nginx). It respects the `X-Forwarded-Proto` header to generate correct redirect URLs with HTTPS.

## Local Development

```bash
pip install -r requirements.txt
ICECAST_RELAYS='relay1.example.com,relay2.example.com' uvicorn app.main:app --reload --port 8080
```

## Project Structure

```
icecast-balancer/
├── app/
│   ├── __init__.py
│   └── main.py
├── Dockerfile
├── docker-compose.yml
├── Pipfile
├── requirements.txt
└── README.md
```

## Contributing

Pull requests are welcome.
