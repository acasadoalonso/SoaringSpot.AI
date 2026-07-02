# SoaringSpot MCP Server Documentation

## Overview

The SoaringSpot MCP (Model Context Protocol) server is an HTTP-based server that wraps the SoaringSpot v1 REST API. It provides authenticated access to gliding competition data including contests, classes, tasks, pilots, and results.

**Server File:** `ss_server.py`  
**Default Port:** 8000 (can be configured)  
**Transport Modes:** HTTP (streamable-http, SSE), stdio

---

## Installation & Dependencies

The server uses:
- `fastmcp` - MCP framework
- `httpx` - Async HTTP client
- Python 3.9+

Install dependencies:
```bash
pip install fastmcp httpx
```

---

## Authentication

The server uses HMAC-SHA256 authentication. Credentials are competition-specific and must be set via environment variables:

```bash
export SOARINGSPOT_CLIENT_ID=" competition_id_xxx"
export SOARINGSPOT_SECRET="your_secret_key"
export SOARINGSPOT_BASE_URL="http://api.soaringspot.com/v1"  # optional, defaults to this
export SOARINGSPOT_COMPNAME="wgc2026"  # optional, for credential loading
```

### Credential Loading from Files

When `SOARINGSPOT_COMPNAME` is set and credentials aren't in environment variables, the server reads from:
```
SoaringSpot/<compname>/clientid
SoaringSpot/<compname>/secretkey
```

Credentials are **per-competition** - each competition has its own client ID and secret.

---

## Usage

### Starting the Server

```bash
# HTTP mode (default, port 8000)
SOARINGSPOT_CLIENT_ID=xxx SOARINGSPOT_SECRET=yyy python ss_server.py

# Override host, port, path
SOARINGSPOT_CLIENT_ID=xxx SOARINGSPOT_SECRET=yyy \
  python ss_server.py --transport http --host 0.0.0.0 --port 9009 --path /soaringspot

# Stdio mode (for Claude Desktop)
SOARINGSPOT_CLIENT_ID=xxx SOARINGSPOT_SECRET=yyy \
  python ss_server.py --transport stdio
```

### MCP Configuration (claude.mcp.json)

```json
{
  "mcpServers": {
    "soaringspot": {
      "type": "http",
      "url": "http://localhost:9009/soaringspot"
    }
  }
}
```

---

## Available Tools

### Utility Tools

| Tool | Description |
|------|-------------|
| `set_compname(compname)` | Load credentials for a specific competition by name |
| `get_credentials()` | Return current client ID and secret key |
| `list_compnames()` | List all competitions handled by this server |
| `get_server_time()` | Get server's UTC time (for HMAC clock skew diagnosis) |

### Contests

| Tool | Description |
|------|-------------|
| `list_contests(id, name, start, end, category, country, limit, page)` | Search and list competitions with filtering |
| `get_contest(id)` | Get full details of a competition |
| `get_contest_classes(id)` | List all classes in a competition |
| `get_contest_downloads(id)` | List airspace/waypoint downloads (cub, openair, gpx, etc.) |
| `get_contest_winners(id)` | Get overall competition winners |

### Classes

| Tool | Description |
|------|-------------|
| `get_class(id)` | Get class details (category, type, etc.) |
| `get_class_contestants(id)` | List pilots in a class |
| `get_class_results(id)` | Get cumulative class standings |
| `get_class_tasks(id)` | List all tasks for a class |

### Contestants

| Tool | Description |
|------|-------------|
| `get_contestant(id)` | Get pilot details (name, glider, nationality, etc.) |

### Tasks

| Tool | Description |
|------|-------------|
| `get_tasks(date, email)` | Get tasks matching filters (defaults to today) |
| `get_task(id)` | Get task details (type, status, distance) |
| `get_task_points(id)` | Get task waypoints/turnpoints |
| `get_task_results(id)` | Get daily results (speed, distance, points per pilot) |
| `get_task_download_xml(id)` | Download task XML for flight computers |
| `get_task_images(id)` | Get map images for a task |

### Flights

| Tool | Description |
|------|-------------|
| `get_flight(id)` | Get flight/IGC data and metadata |
| `get_flight_from_url(url)` | Get flight data from a URL string |

### Locations & Images

| Tool | Description |
|------|-------------|
| `get_location(id)` | Get location details (coordinates, airfield) |
| `get_image(id)` | Get metadata for a map image |

---

## Data Model

```
Contest (competition event)
 └── Class (competition category: Club, Standard, 18m, Open, etc.)
      ├── Contestants (pilots)
      ├── Tasks (daily competition days)
      │    ├── Points (waypoints/turnpoints)
      │    ├── Results (daily scoring per pilot)
      │    ├── Images (map images)
      │    └── Downloads (XML for flight computers)
      └── Results (cumulative standings)
 └── Winners (overall champions)
```

---

## Authentication Header Format

The server builds HMAC-SHA256 authorization headers:

```
Authorization: <apiurl>v1/hmac/v1 ClientID="<client_id>",
                 Signature="<base64(hmac_sha256)>",
                 Nonce="<base64(random)>",
                 Created="<YYYY-MM-DDTHH:MM:SSZ>"
```

---

## Error Handling

- **Auth errors:** Incorrect credentials result in 401/403 responses
- **Clock skew:** Server rejects requests >5 minutes off from server time
- **Missing credentials:** Raises `RuntimeError` if env vars or file credentials missing
- **HTTP errors:** Raised as exceptions with status codes

---

## Example Workflow

1. **Discover competitions:**
   ```python
   list_contests(country="PL", category="glider")
   ```

2. **Get competition details:**
   ```python
   get_contest(5249)  # WGC 2026
   ```

3. **List classes and drill down:**
   ```python
   get_contest_classes(5249)       # Get class IDs
   get_class_results(10053)        # Open class standings
   get_class_tasks(10053)          # Tasks for Open class
   ```

4. **Get task details:**
   ```python
   get_task(10541334541)           # Task details
   get_task_points(10541334541)    # Waypoints
   get_task_results(10541334541)   # Daily results
   get_task_download_xml(10541334541)  # XML for flight computer
   ```

---

## Notes

- Credentials are **per-competition** - each competition issues its own client ID/secret
- The `get_contest(id)` endpoint returns `/` instead of `/contests/{id}` - this may be a bug
- Flight IDs are large integers returned from `get_task_results`
- XML downloads require specific Accept headers (`application/xml`)
