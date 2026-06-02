#!/usr/bin/env python3
"""
SoaringSpot MCP Server
======================
Wraps the SoaringSpot v1 REST API (https://api.soaringspot.com/v1/)
using HMAC-SHA256 authentication as documented at:
  http://download.naviter.com/soaringspot/api/index.html

Transport: HTTP (streamable-http) by default, also supports stdio and SSE.

Usage:
  # HTTP (default, port 8000)
  SOARINGSPOT_CLIENT_ID=xxx SOARINGSPOT_SECRET=yyy python server.py

  # Override host / port / transport
  SOARINGSPOT_CLIENT_ID=xxx SOARINGSPOT_SECRET=yyy \
    python server.py --transport http --host 0.0.0.0 --port 9000

  # stdio (for Claude Desktop)
  SOARINGSPOT_CLIENT_ID=xxx SOARINGSPOT_SECRET=yyy \
    python server.py --transport stdio
"""

import argparse
import base64
import hashlib
import hmac
import os
import sys
import secrets
import string
from typing import Annotated, Optional
import time
import datetime
import httpx
from fastmcp import FastMCP

# ── Configuration ─────────────────────────────────────────────────────────────

CLIENT_ID = os.environ.get("SOARINGSPOT_CLIENT_ID", "")
SECRET    = os.environ.get("SOARINGSPOT_SECRET", "").encode()
BASE_URL  = os.environ.get("SOARINGSPOT_BASE_URL", "http://api.soaringspot.com/v1")
COMPNAME  = os.environ.get("SOARINGSPOT_COMPNAME", "")
prt=False
apiurl   = "http://api.soaringspot.com/"        # soaringspot API URL
rel      = "v1"   
#utc = datetime.datetime.utcnow()
utc = datetime.datetime.now(datetime.UTC)
date = utc.strftime("%Y-%m-%dT%H:%M:%SZ")
if not CLIENT_ID or not SECRET:
    # 
    if prt:
       print("Reading the clientid/secretkey from the SoaringSpot directory")
    # if client/screct keys are not in the config file, read it for SoaringSpot directory
    f = open("SoaringSpot/"+COMPNAME+"/clientid") 	# open the file with the client id
    client = f.read()               	    # read it
    CLIENT_ID = client.rstrip('\n') 		# clear the whitespace at the end
    f = open("SoaringSpot/"+COMPNAME+"/secretkey") 	# open the file with the secret key
    secretkey = f.read()            	# read it
           					# clear the whitespace at the end
    SECRET = secretkey.rstrip('\n').encode(encoding='utf-8')
    print ("SoaringSpot Credentials for comp:", COMPNAME, "\n", CLIENT_ID, "\n", SECRET)
    if not CLIENT_ID or not SECRET:
       raise RuntimeError(
        "Environment variables SOARINGSPOT_CLIENT_ID and SOARINGSPOT_SECRET are required."
    )

# ── HMAC auth helpers ─────────────────────────────────────────────────────────

_NONCE_CHARS = string.ascii_letters + string.digits + "!#$%&'()*+,-./:;<=>?@[]^_`{|}~"

def _make_nonce(length: int = 28) -> str:
    """Return a random printable-ASCII nonce (>16 bytes, as required by the API)."""
    return "".join(secrets.choice(_NONCE_CHARS) for _ in range(length))


def _auth_header() -> str:
    """Build the HMAC-SHA256 Authorization header for one request."""
    # The API requires a fresh `Created` timestamp per request (it rejects
    # stale ones), so compute it here rather than reusing a module-level value.
    date    = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    nonce   = base64.b64encode(os.urandom(36))
    message = nonce+date.encode(encoding='utf-8')+CLIENT_ID.encode(encoding='utf-8')   # build the message
                                                # and the message digest
    digest = hmac.new(SECRET, msg=message, digestmod=hashlib.sha256).digest()
    signature = str(base64.b64encode(digest).decode())   # build the digital signature
                                                # the AUTHORIZATION ID is built now

    auth = apiurl+rel+'/hmac/v1 ClientID="'+CLIENT_ID+'",Signature="' + \
    signature+'",Nonce="'+nonce.decode(encoding='utf-8')+'",Created="'+date+'"'
    #print ("URLauth:", auth, type(auth), file=sys.stderr)
    return (auth)


def _headers() -> dict[str, str]:
    return {
        "Accept":        "application/hal+json",
        "Authorization": _auth_header(),
    }


# ── Low-level HTTP helpers ────────────────────────────────────────────────────

async def _get(path: str, params: Optional[dict] = None) -> dict:
    """Authenticated GET → dict (HAL+JSON)."""
    #print (">>>>>>>> Header:", _headers(), file=sys.stderr)
    clean = {k: v for k, v in (params or {}).items() if v is not None}
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            BASE_URL + path,
            params=clean,
            headers=_headers(),
            follow_redirects=True,
            timeout=30,
        )
    resp.raise_for_status()
    return resp.json()


async def _get_xml(path: str) -> str:
    """Authenticated GET → raw XML string."""
    hdrs = _headers()
    hdrs["Accept"] = "application/xml, text/xml"
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            BASE_URL + path,
            headers=hdrs,
            follow_redirects=True,
            timeout=30,
        )
    resp.raise_for_status()
    return resp.text


async def _server_time() -> str | None:
    """Return the X-Server-Time header value from the /time endpoint."""
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            BASE_URL + "/time",
            headers=_headers(),
            timeout=10,
        )
    return resp.headers.get("X-Server-Time")


# ── FastMCP server ────────────────────────────────────────────────────────────

mcp = FastMCP(
    name="soaringspot",
    instructions=(
        "Tools to query the SoaringSpot gliding competition platform. "
        "Use list_contests to discover competitions, then drill down via "
        "get_contest_classes, get_class_results, get_task_points, etc."
    ),
)

# ─── Utility ──────────────────────────────────────────────────────────────────

@mcp.tool
async def get_server_time() -> dict:
    """
    Return the SoaringSpot server's current UTC time.
    Useful for diagnosing clock-skew issues with HMAC authentication
    (requests are rejected if >5 minutes off).
    """
    t = await _server_time()
    return {"server_time": t}


# ─── Contests ─────────────────────────────────────────────────────────────────

@mcp.tool
async def list_contests(
    id:       Annotated[Optional[str], "Filter by competition ID."] = None,
    name:     Annotated[Optional[str], "Filter by competition name (partial match)."] = None,
    start:    Annotated[Optional[str], "Start-date filter (YYYY-MM-DD), may be prefixed with <,>,<=,>=."] = None,
    end:      Annotated[Optional[str], "End-date filter (YYYY-MM-DD), may be prefixed with <,>,<=,>=."] = None,
    category: Annotated[Optional[str], "Category: any | glider | hang_glider | paraglider"] = None,
    country:  Annotated[Optional[str], "2-letter ISO country code, e.g. DE, US, FR."] = None,
    limit:    Annotated[Optional[int], "Results per page (default 20)."] = None,
    page:     Annotated[Optional[int], "Page number (default 1)."] = None,
) -> dict:
    """
    List or search competitions on SoaringSpot.
    Returns the default list when no filters are provided.
    Supports paging via `limit` and `page`.
    """
    return await _get("/contests", {
        "id": id, "name": name, "start": start, "end": end,
        "category": category, "country": country,
        "limit": limit, "page": page,
    })


@mcp.tool
async def get_contest(
    id: Annotated[int, "Contest ID."],
) -> dict:
    """Get full details of a specific competition (name, dates, location, category, etc.)."""
    #return await _get(f"/contests/{id}")
    return await _get(f"/")


@mcp.tool
async def get_contest_classes(
    id: Annotated[int, "Contest ID."],
) -> dict:
    """Get all glider classes (Standard, 18m, Open, Club, etc.) in a competition."""
    return await _get(f"/contests/{id}/classes")


@mcp.tool
async def get_contest_downloads(
    id: Annotated[int, "Contest ID."],
) -> dict:
    """
    List available airspace and waypoint file downloads for a competition.
    Formats include: airspace/cub, airspace/txt_openair, waypoint/cup,
    waypoint/da4_lxnav, waypoint/gpx_garmin, and more.
    """
    return await _get(f"/contests/{id}/downloads")


@mcp.tool
async def get_contest_winners(
    id: Annotated[int, "Contest ID."],
) -> dict:
    """Get the overall winners of a competition."""
    return await _get(f"/contests/{id}/winners")


# ─── Classes ──────────────────────────────────────────────────────────────────

@mcp.tool
async def get_class(
    id: Annotated[int, "Class ID."],
) -> dict:
    """
    Get details of a specific competition class.
    Includes category (glider/hang_glider/paraglider) and type
    (standard, 15_meter, 18_meter, open, club, double_seater, etc.).
    """
    return await _get(f"/classes/{id}")


@mcp.tool
async def get_class_contestants(
    id: Annotated[int, "Class ID."],
) -> dict:
    """Get the list of pilots/contestants registered in a competition class."""
    return await _get(f"/classes/{id}/contestants")


@mcp.tool
async def get_class_results(
    id: Annotated[int, "Class ID."],
) -> dict:
    """Get the overall standings/results for a competition class (cumulative points)."""
    return await _get(f"/classes/{id}/results")


@mcp.tool
async def get_class_tasks(
    id: Annotated[int, "Class ID."],
) -> dict:
    """Get all scored tasks (competition days) for a class."""
    return await _get(f"/classes/{id}/tasks")


# ─── Contestants ──────────────────────────────────────────────────────────────

@mcp.tool
async def get_contestant(
    id: Annotated[int, "Contestant ID."],
) -> dict:
    """Get details of a specific pilot/contestant (name, glider, registration, etc.)."""
    return await _get(f"/contestants/{id}")


# ─── Tasks ────────────────────────────────────────────────────────────────────

@mcp.tool
async def get_tasks(
    date:  Annotated[Optional[str], "ISO date (YYYY-MM-DD). Defaults to today if omitted."] = None,
    email: Annotated[Optional[str], "Filter tasks by pilot's registered email address."] = None,
) -> dict:
    """
    Get tasks matching the given filters.
    Defaults to today's tasks when no filter is provided.
    Useful for retrieving the current day's task across all competitions.
    """
    return await _get("/tasks", {"date": date, "email": email})


@mcp.tool
async def get_task(
    id: Annotated[int, "Task ID."],
) -> dict:
    """
    Get details of a specific task (competition day).
    Includes: task_type (AAT, FAI triangle, straight distance, …),
    result_status (preliminary/unofficial/official/cancelled/practice),
    distance, and more.
    Negative task_number means it's a practice day.
    """
    return await _get(f"/tasks/{id}")


@mcp.tool
async def get_task_download_xml(
    id: Annotated[int, "Task ID."],
) -> str:
    """
    Download the task as XML — the format used by navigation devices
    (Oudie, XCSoar, LX9000, LK8000, iGlide, etc.).
    The XML includes waypoints, observation zones, changelog notes, and scoring details.
    """
    return await _get_xml(f"/tasks/{id}/download")


@mcp.tool
async def get_task_images(
    id: Annotated[int, "Task ID."],
) -> dict:
    """Get all map images associated with a task."""
    return await _get(f"/tasks/{id}/images")


@mcp.tool
async def get_task_points(
    id: Annotated[int, "Task ID."],
) -> dict:
    """
    Get the waypoints/turn-points that define a task.
    Each point includes type (start/finish/point/takeoff/landing/marker),
    observation zone settings (oz_type, radius1, radius2, angles), and coordinates.
    """
    return await _get(f"/tasks/{id}/points")


@mcp.tool
async def get_task_results(
    id: Annotated[int, "Task ID."],
) -> dict:
    """Get the daily results for a specific task (speed, distance, points per pilot)."""
    return await _get(f"/tasks/{id}/results")


# ─── Flights ──────────────────────────────────────────────────────────────────

@mcp.tool
async def get_flight(
    id: Annotated[int, "Result ID (from task results)."],
) -> dict:
    """
    Get the flight/IGC data and metadata for a specific result.
    Use result IDs obtained from get_task_results.
    """
    return await _get(f"/flights/{id}")


# ─── Locations & Images ───────────────────────────────────────────────────────

@mcp.tool
async def get_location(
    id: Annotated[int, "Location ID."],
) -> dict:
    """Get the geographic location details of a competition (coordinates, airfield name, etc.)."""
    return await _get(f"/locations/{id}")


@mcp.tool
async def get_image(
    id: Annotated[int, "Image ID."],
) -> dict:
    """Get metadata for a specific task map image."""
    return await _get(f"/images/{id}")


# ── CLI entry-point ───────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="SoaringSpot MCP server",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--transport",
        choices=["http", "streamable-http", "sse", "stdio"],
        default="http",
        help="MCP transport to use.",
    )
    parser.add_argument("--host", default="127.0.0.1", help="Bind host (HTTP/SSE only).")
    parser.add_argument("--port", type=int, default=8000, help="Bind port (HTTP/SSE only).")
    parser.add_argument("--path", default="/mcp", help="Endpoint path (HTTP/SSE only).")
    args = parser.parse_args()

    if args.transport == "stdio":
        mcp.run(transport="stdio")
    else:
        mcp.run(
            transport=args.transport,
            host=args.host,
            port=args.port,
            path=args.path,
        )


if __name__ == "__main__":
    try:
       main()
    except KeyboardInterrupt:
        print ("Good bye ...\n")
        exit(0)
