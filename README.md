# SoaringSpot MCP Server (Python / FastMCP)

An MCP server wrapping the [SoaringSpot public API](http://download.naviter.com/soaringspot/api/index.html) — the gliding competition platform by Naviter — built with **FastMCP** and supporting HTTP, SSE, and stdio transports.

## Requirements

- Python 3.11+
- `fastmcp >= 3.0`, `httpx`

## Install

```bash
pip install fastmcp httpx
```

## Credentials

In your SoaringSpot competition admin panel go to **Edit Competition → API Keys** to generate a **Client ID** and **Secret**.

```bash
export SOARINGSPOT_CLIENT_ID="your-client-id"
export SOARINGSPOT_SECRET="your-secret"

```
The credentials for an specific competitions are under the directory SoaringSpot 
and within that directory on a subdirectory that matches the name with the 
competition name, for example:
SoaringSpot/wgc2026/clientid or
SoaringSpot/wgc2026/secretkey

Optionally override the base URL (e.g. for the test environment):
```bash
export SOARINGSPOT_BASE_URL="https://api.test.soaringspot.com/v1"
```

---

## Running

### HTTP (default — streamable-http, port 8000)

```bash
python ss_server.py
# → http://127.0.0.1:8000/mcp
```

### Custom host / port / path

```bash
python ss_server.py --host 0.0.0.0 --port 9000 --path /soaringspot
```

### SSE transport

```bash
python ss_server.py --transport sse --port 8000
```

### stdio (Claude Desktop)

```bash
python ss_server.py --transport stdio
```

---

## Claude Desktop config (stdio)

```json
{
  "mcpServers": {
    "soaringspot": {
      "command": "python",
      "args": ["/absolute/path/to/soaringspot_mcp/ss_server.py", "--transport", "stdio"],
      "env": {
        "SOARINGSPOT_CLIENT_ID": "<your-client-id>",
        "SOARINGSPOT_SECRET": "<your-secret>"
      }
    }
  }
}
```

## Claude Desktop config (HTTP)

Start the server first, then point Claude at it:

```json
{
  "mcpServers": {
    "soaringspot": {
      "url": "http://127.0.0.1:8000/mcp"
    }
  }
}
```

---

## Available Tools

| Tool | Description |
|------|-------------|
| `list_contests` | Search competitions by name, country, date range, category; supports paging |
| `get_contest` | Full details of one competition |
| `get_contest_classes` | All glider classes in a competition |
| `get_contest_downloads` | Airspace & waypoint file links |
| `get_contest_winners` | Overall winners |
| `get_class` | Class details (type, category) |
| `get_class_contestants` | Pilots registered in a class |
| `get_class_results` | Cumulative standings for a class |
| `get_class_tasks` | All scored days for a class |
| `get_contestant` | Individual pilot details |
| `get_tasks` | Today's tasks (or filter by date / pilot email) |
| `get_task` | Task details (type, status, distances) |
| `get_task_download_xml` | Task XML for nav devices (Oudie, XCSoar, LX9000…) |
| `get_task_images` | Task map images |
| `get_task_points` | Turnpoints with observation zones |
| `get_task_results` | Daily results per pilot |
| `get_flight` | IGC flight metadata for a result |
| `get_location` | Competition airfield location |
| `get_image` | Image metadata |
| `get_server_time` | Server UTC time (for clock-sync / auth debugging) |

---

## Authentication details

Every request is signed with **HMAC-SHA256**:

```
Authorization: http://api.soaringspot.com/v1/hmac/v1
  ClientID="<id>", Signature="<sig>", Nonce="<nonce>", Created="<ISO-UTC>"

Signature = base64(HMAC-SHA256(nonce + created + clientId, secret))
```

The nonce is generated fresh per request using `secrets`; the timestamp must be within ±5 minutes of the server. Use `get_server_time` to diagnose drift.

---

## Notes

- The API uses **HAL+JSON** (`application/hal+json`). Responses include `_links` you should follow rather than hard-coding URIs.
- `get_task_download_xml` returns raw XML intended for glider navigation devices.
- Flight upload (`POST /contests/{id}/flights`) is intentionally omitted — it requires `multipart/form-data` and is normally handled by scoring software like SeeYou Competition.
