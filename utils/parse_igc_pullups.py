#!/usr/bin/env python3
"""
IGC flight log parser -- detects excessive pull-ups on final glide.

Criteria (all must be met simultaneously):
  1. Within the last NN minutes of the flight.
  2. GPS altitude below NN meters.
  3. Peak vertical speed between two consecutive B-fixes (barometric) exceeds
     the configurable threshold.
  4. Total height gained is more than NN meters.
  5. Average vertical speed of pullup event last more than NN seconds.
  6. Average vertical speed of pullup event exceeds
     the configurable threshold.

Usage:
  python parse_igc_pullups.py                    # scan current directory
  python parse_igc_pullups.py /path/to/dir       # scan a directory
  python parse_igc_pullups.py flight.igc         # check a single file
  python parse_igc_pullups.py flight.igc --t1 3  # custom threshold
"""

import argparse
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional

# ---------------------------------------------------------------------------
# IGC parsing helpers
# ---------------------------------------------------------------------------

def parse_hms(hhmmss: str) -> int:
    """Return seconds-since-midnight for a 6-digit HHMMSS string."""
    return int(hhmmss[0:2]) * 3600 + int(hhmmss[2:4]) * 60 + int(hhmmss[4:6])


def parse_b_record(line: str) -> Optional[Dict]:
    """
    Parse an IGC B-record.  Returns a dict or None on parse failure.

    B HHMMSS DDMMmmmN/S DDDMMmmmE/W A PPPPP GGGGG [optional]
    Positions (0-indexed):
      0      : 'B'
      1-6    : HHMMSS
      7-14   : DDMMmmmN/S   (lat)
      15-23  : DDDMMmmmE/W  (lon)
      24     : Fix validity A/V
      25-29  : pressure altitude (5 digits, metres)
      30-34  : GPS altitude     (5 digits, metres)
    """
    if len(line) < 35 or line[0] != 'B':
        return None
    try:
        time_s = parse_hms(line[1:7])

        lat_deg = int(line[7:9])
        lat_min = int(line[9:11]) + int(line[11:14]) / 1000.0
        lat = lat_deg + lat_min / 60.0
        if line[14] == 'S':
            lat = -lat

        lon_deg = int(line[15:18])
        lon_min = int(line[18:20]) + int(line[20:23]) / 1000.0
        lon = lon_deg + lon_min / 60.0
        if line[23] == 'W':
            lon = -lon

        validity = line[24]
        baro_alt = int(line[25:30])
        gps_alt  = int(line[30:35])

        return {
            'time_s':   time_s,
            'lat':      lat,
            'lon':      lon,
            'validity': validity,
            'baro_alt': baro_alt,
            'gps_alt':  gps_alt,
        }
    except (ValueError, IndexError):
        return None


def seconds_to_utc(s: int) -> str:
    """Format seconds-since-midnight as HH:MM:SS UTC."""
    h   = s // 3600
    m   = (s % 3600) // 60
    sec = s % 60
    return f"{h:02d}:{m:02d}:{sec:02d}"

# ---------------------------------------------------------------------------
# Core analysis
# ---------------------------------------------------------------------------

def analyse_file(igc_path: str) -> Optional[Dict]:
    """
    Parse one IGC file and return the worst (highest VS) pull-up event,
    or None if no qualifying event is found.

    Returned dict contains: file, utc_time, vertical_speed, height_gained.
    """
    fixes = []

    global args

    with open(igc_path, 'r', errors='replace') as fh:
        for line in fh:
            line = line.strip()
            if line.startswith('B'):
                fix = parse_b_record(line)
                if fix is not None:
                    fixes.append(fix)

    if len(fixes) < 2:
        return None

    last_time    = fixes[-1]['time_s']
    window_start = last_time - 5 * 60   # last 5 minutes

    candidates = []   # all qualifying pairs
    n = len(fixes)

    for i in range(n - 1):
        f0 = fixes[i]
        f1 = fixes[i + 1]

        # Criterion 1: last 5 minutes
        if f0['time_s'] < window_start:
            continue

        # Criterion 2: GPS altitude below NN m
        if f0['gps_alt'] >= args.alt:
            continue

        # Criterion 3: barometric vertical speed > args.t1
        dt = f1['time_s'] - f0['time_s']
        if dt <= 0:
            continue
        vs = (f1['baro_alt'] - f0['baro_alt']) / dt   # m/s

        if vs <= args.t1:
            continue

        candidates.append((i, vs))

    if not candidates:
        return None

    # Pick the pair with the highest vertical speed
    peak_i, peak_vs = max(candidates, key=lambda x: x[1])

    # Extend run: walk backward while vs >= 0
    run_start = peak_i
    while run_start > 0:
        prev = fixes[run_start - 1]
        curr = fixes[run_start]
        dt_b = curr['time_s'] - prev['time_s']
        if dt_b <= 0:
            break
        if (curr['baro_alt'] - prev['baro_alt']) / dt_b < 0:
            break
        run_start -= 1

    # Walk forward while vs >= 0
    run_end = peak_i + 1
    while run_end < n - 1:
        curr = fixes[run_end]
        nxt  = fixes[run_end + 1]
        dt_f = nxt['time_s'] - curr['time_s']
        if dt_f <= 0:
            break
        if (nxt['baro_alt'] - curr['baro_alt']) / dt_f < 0:
            break
        run_end += 1

    run_alts     = [fixes[j]['baro_alt'] for j in range(run_start, run_end + 1)]
    height_gained = max(run_alts) - min(run_alts)
    run_time     = fixes[run_end]['time_s'] - fixes[run_start]['time_s']
    run_avg_vs   = height_gained / run_time

    if (   run_avg_vs < args.t2
       and peak_vs < args.t1 ):
        return None

    if (   run_time < args.duration
       or  height_gained < args.gain):
        return None

    return {
        'file':           os.path.basename(igc_path),
        'utc_time':       seconds_to_utc(fixes[peak_i]['time_s']),
        'peak_vs':        round(peak_vs, 2),
        'height_gained':  height_gained,
        'duration':       run_time,
        'avg_vs':         run_avg_vs,
    }

# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def collect_igc_files(target: Path) -> List[Path]:
    """Return a sorted, deduplicated list of IGC files from a file or dir."""
    if target.is_file():
        if target.suffix.lower() == '.igc':
            return [target]
        sys.exit(f"Error: '{target}' is not an IGC file.")

    if target.is_dir():
        raw = sorted(target.glob('*.igc')) + sorted(target.glob('*.IGC'))
        seen = set()
        unique = []
        for f in raw:
            key = str(f).lower()
            if key not in seen:
                seen.add(key)
                unique.append(f)
        return unique

    sys.exit(f"Error: '{target}' is not a file or directory.")


def main():
    global args

    parser = argparse.ArgumentParser(
        description='Detect excessive pull-ups on final glide in IGC flight logs.'
    )
    parser.add_argument(
        'path',
        nargs='?',
        default='.',
        help='IGC file or directory to scan (default: current directory)'
    )
    parser.add_argument(
        '--t1',
        type=float,
        default=6.0,
        help='Peak VS threshold in [m/s] (default: 6.0)'
    )
    parser.add_argument(
        '--t2',
        type=float,
        default=4.0,
        help='Average VS threshold [m/s] (default: 4.0)'
    )
    parser.add_argument(
        '--alt',
        type=int,
        default=900,
        help='Max altitude [m] (default: 900)'
    )
    parser.add_argument(
        '--duration',
        type=int,
        default=3,
        help='Minimal pullup duration [s] (default: 3)'
    )
    parser.add_argument(
        '--gain',
        type=int,
        default=20,
        help='Minimum total gained height [m] (default: 20)'
    )

    parser.add_argument(
        '--mins',
        type=int,
        default=5,
        help='Minutes at the end of flight to check (default: 10)'
    )


    args = parser.parse_args()

    target = Path(args.path)
    igc_files = collect_igc_files(target)

    if not igc_files:
        print(f"No IGC files found in '{target}'.")
        return

    label = str(target) if target.is_file() else f"{len(igc_files)} IGC file(s) in '{target}'"
    print(f"Scanning {label} -- thresholds: {args.t1} Peak / {args.t2} Avg m/s")
    print(f"GPS alt < {args.alt} m, last {args.mins} min, "
          f"min. duration {args.duration}s\n")

    COL_FILE = 30
    COL_TIME =  8
    COL_GAIN =  7
    COL_DUR  =  7
    COL_AVG  =  7
    COL_VS   =  8
    header = (f"{'File':<{COL_FILE}}  {'Time UTC':>{COL_TIME}}  "
              f"{'Gain':>{COL_GAIN}}  "
              f"{'Durat.':>{COL_DUR}}  "
              f"{'Avg vs':>{COL_AVG}}  "
              f"{'Peak vs':>{COL_VS}}"
    )
    separator = "-" * len(header)
    print(header)
    print(separator)

    total_events = 0

    for igc_path in igc_files:
        try:
            ev = analyse_file(str(igc_path))
        except Exception as exc:
            print(f"[WARN] Could not parse {igc_path.name}: {exc}")
            continue

        if ev is None:
            continue

        total_events += 1
        fname = ev['file']
        if len(fname) > COL_FILE:
            fname = fname[:COL_FILE - 1] + "~"
        print(f"{fname:<{COL_FILE}}  {ev['utc_time']:>{COL_TIME}}  "
              f"{ ('%dm' % ev['height_gained']):>{COL_GAIN}}  "
              f"{ev['duration']:>{COL_DUR}}  "
              f"{ev['avg_vs']:>+{COL_AVG}.1f}  "
              f"{ev['peak_vs']:>+{COL_VS}.1f}"
        )

    print(separator)
    if total_events == 0:
        print("(no excessive pull-ups detected)")
    else:
        print(f"Total files with excessive pull-up: {total_events}")


if __name__ == '__main__':
    main()
