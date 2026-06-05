#!/usr/bin/env python3
"""
IGC filename checker.

Validates that IGC filenames are consistent with the header data
(flight date and serial number) inside each file.

Supports both short (YMDCXXXF.IGC) and long filename formats as defined
in the IGC FR Technical Specification.  The long format accepts either a
3-character or 6-character serial number field:
    YYYY-MM-DD-MMM-XXX-FF.IGC   (standard 3-char serial)
    YYYY-MM-DD-MMM-XXXXXX-FF.IGC  (extended 6-char serial)

Output is always written in full to a log file:
  - Current directory  ->  check.log
  - Named directory    ->  check_<DIRNAME>.log
On the console only warnings and errors are printed; if there are none
the script runs silently.
"""

import re
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Optional


# ---------------------------------------------------------------------------
# Manufacturer code translation: single-letter (short filename) -> 3-letter
# (long filename).  Extend this dict as needed.
# ---------------------------------------------------------------------------

MANUFACTURER_CODES = {
    "I": "ACT",  # Aircotec
    "C": "CAM",  # Cambridge
    "D": "DSX",  # Data Swan
    "E": "EWA",  # EW Avionics
    "F": "FIL",  # Filser
    "G": "FLA",  # FLARM
    "A": "GCS",  # Garrecht
    "M": "IMI",  # IMI
    "L": "LXN",  # LX Navigatiom
    "V": "LXV",  # LXNAV
    "N": "NTE",  # New Technologies
    "K": "NKL",  # Nielsen Kellerman
    "P": "PES",  # Peschges
    "R": "PRT",  # PressFinish Electronics
    "H": "SCH",  # Scheffel
    "S": "SDI",  # Streamline Data Instruments
    "Z": "ZAN",  # Zander
}

DATA_GAP_B = 30
DATA_GAP_A = 60


# ---------------------------------------------------------------------------
# Logger -- writes everything to file, warnings/errors to console too
# ---------------------------------------------------------------------------

class Logger:
    """
    Dual-output logger.  Every message goes to the log file; only lines that
    contain '[WARN] ' or '[ERROR]' are also echoed to stdout.
    """
    CONSOLE_TRIGGERS = ("[WARN]", "[ERROR]", "[SKIP]")

    _fh = None

    def __init__(self, log_path):
        if log_path != None:
            self._fh = open(log_path, "w", encoding="utf-8")

    def __call__(self, msg=""):
        if self._fh is not None:
            self._fh.write(msg + "\n")
            self._fh.flush()
            if any(t in msg for t in self.CONSOLE_TRIGGERS):
                print(msg)
        else:
            print(msg)

    def close(self):
        if self._fh is not None:
            self._fh.close()


# Module-level logger; set in main() before any checks run.
log = None


# ---------------------------------------------------------------------------
# Base-36 decoding helpers (used in short filenames)
# ---------------------------------------------------------------------------

# Maps encoded character -> integer value for year/month/day fields
# Digits 1-9 -> 1-9; A=10, B=11 ... V=31
_B36_DIGIT_MAP = {str(i): i for i in range(10)}
_B36_DIGIT_MAP.update({chr(ord("A") + i): 10 + i for i in range(26)})


def _decode_b36_digit(ch):
    return _B36_DIGIT_MAP.get(ch.upper())


def _decode_year_digit(ch):
    v = _B36_DIGIT_MAP.get(ch.upper())
    return v if v is not None and v <= 9 else None


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class HeaderInfo:
    fr: str            # 3-char manufacturer code, dash, 3- or 6-char alphanumeric S/N from A record
    flight_date: date  # date from HFDTE record
    cid: str           # competition ID (optional)


@dataclass
class FilenameInfo:
    format: str        # "short" or "long"
    fr: str            # 3-char manufacturer code, dash, 3- or 6-char alphanumeric S/N from A record
    flight_date: date
    flight_number: int


# ---------------------------------------------------------------------------
# Header parsing
# ---------------------------------------------------------------------------

def _parse_hfdte(line):
    """Parse HFDTE record; handles both HFDTEDDMMYY and HFDTEDATE:DDMMYY,NN."""
    line = line.strip()
    m = re.match(r"HFDTE(?:DATE:)?(\d{6})", line, re.IGNORECASE)
    if not m:
        return None
    raw = m.group(1)
    dd, mm, yy = int(raw[0:2]), int(raw[2:4]), int(raw[4:6])
    year = 2000 + yy if yy < 90 else 1900 + yy
    try:
        return date(year, mm, dd)
    except ValueError:
        return None


def _parse_hfcid(line):
    """Parse HFCID record"""
    line = line.strip()
    m = re.match(r"HFCID\w*:(\w+)", line, re.IGNORECASE)
    if not m:
        return ''
    return m.group(1)


def parse_header(path):
    """
    Read an IGC file and extract serial number and flight date from its header.
    Returns None if mandatory records are missing or malformed.
    """
    serial = None
    manufacturer = None
    flight_date = None
    cid = ''

    if path.stat().st_size == 0:
        log("[ERROR] {:<28}     -- empty file".format(path.name))
        return None

    try:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            for raw_line in fh:
                line = raw_line.strip()
                if not line:
                    continue

                # A record must be the very first non-empty line
                if serial is None and manufacturer is None:
                    if line[0] != "A":
                        log("[ERROR] {:<28}     -- first record is not an A record".format(path.name))
                        return None
                    if len(line) < 7:
                        log("[ERROR] {:<28}     -- A record too short: {!r}".format(path.name, line))
                        return None
                    manufacturer = line[1:4].upper()
                    # Use 6-char serial if positions 4-9 are all alphanumeric and
                    # not immediately followed by "FLIGHT" (e.g. ALXVN5LFLIGHT:1).
                    if (len(line) >= 10 and line[4:10].isalnum()
                            and not line[7:].upper().startswith("FLIGHT")):
                        serial = line[4:10].upper()
                    else:
                        serial = line[4:7].upper()
                    continue

                # HFDTE record
                if line.upper().startswith("HFDTE"):
                    # check for duplicate HFDTE record
                    if flight_date is not None:
                        continue
                    flight_date = _parse_hfdte(line)
                    if flight_date is None:
                        log("[WARN]  {:<28}     -- could not parse HFDTE record: {!r}".format(
                                     path.name, line)
                        )

                # HFCID record
                if line.upper().startswith("HFCID"):
                    cid = _parse_hfcid(line)

                # End of file header
                if line.upper().startswith("C") or line.upper().startswith("B"):
                    break


    except OSError as exc:
        log("[ERROR] {:<28}     -- cannot read file: {}".format(path.name, exc))
        return None

    if serial is None:
        log("[ERROR] {:<28}     -- missing A record".format(path.name))
        return None
    if flight_date is None:
        log("[ERROR] {:<28}     -- missing or unreadable HFDTE record".format(path.name))
        return None

    return HeaderInfo(fr=manufacturer+'-'+serial, flight_date=flight_date, cid=cid)


# ---------------------------------------------------------------------------
# Trailing data check
# ---------------------------------------------------------------------------

def check_trailing_data(path, cid):
    """
    Warn if non-empty lines (other than G, M, L, N) appear after the first G record.
    Returns True if clean.
    """
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            lines = fh.readlines()
    except OSError as exc:
        log("[ERROR] {:<28}     -- cannot read file: {}".format(path.name, exc))
        return False

    first_g_index = None
    for i, raw_line in enumerate(lines):
        if raw_line.upper().startswith("G"):
            first_g_index = i
            break

    if first_g_index is None:
        log(
            "[WARN]  {:<28} {:<4}-- no security G section found".format(
                path.name, cid)
        )
        return False

    trailing = [
        ln.rstrip("\r\n") for ln in lines[first_g_index + 1:]
        if ln.strip() and ln[0].upper() not in ("G", "M", "L", "N")
    ]
    if trailing:
        log(
            "[WARN]  {:<28} {:<4}-- {} extra line(s) after G section".format(
                path.name, cid, len(trailing))
        )
        return False
    return True


# ---------------------------------------------------------------------------
# Forbidden string check
# ---------------------------------------------------------------------------

_FORBIDDEN_STRINGS = ("AHRSON",)


def check_forbidden_strings(path, cid):
    """
    Warn if any line contains 'AHRSON' or 'BFION'.
    Returns True if clean.
    """
    ok = True
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            for lineno, raw_line in enumerate(fh, 1):
                upper = raw_line.upper()
                for token in _FORBIDDEN_STRINGS:
                    if token in upper:
                        log(
                            "[WARN]  {:<28} {:<4}-- '{}' found on line {}".format(
                                path.name, cid, token, lineno)
                        )
                        ok = False
    except OSError as exc:
        log("[ERROR] {:<28}     -- cannot read file: {}".format(path.name, exc))
        return False
    return ok


def _parse_time(str):
    """
    Change HHMMSS to seconds from midnight
    """
    try:
        h, m, s = int(str[0:2]), int(str[2:4]), int(str[4:6])
        return (3600 * h + 60 * m + s)

    except:
        return None


def check_blind_flying(path, cid):
    """
    Warn if 'BFION' event is found
    Returns True if clean.
    """
    ok = True
    bfi_start = None

    try:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            for raw_line in fh:
                line = raw_line.strip().upper()
                if not line:
                    continue

                if not line.startswith("E"):
                    continue

                if line[7:12] == 'BFION' and bfi_start == None:
                    bfi_start = line[1:7]
                    ok = False
                    continue

                if line[7:13] == 'BFIOFF' and bfi_start != None:
                    try:
                        duration = _parse_time(line[1:7]) - _parse_time(bfi_start)
                    except:
                        duration = "?"

                    log("[WARN]  {:<28} {:<4}-- BFI enabled for {}s at {} UTC".format(
                                path.name, cid, duration, bfi_start)
                    )
                    bfi_start = None
                    continue


        # End of file reached with BFI enabled
        if bfi_start != None:
            log("[WARN]  {:<28} {:<4}-- BFI enabled at {} UTC till end of file".format(
                         path.name, cid, bfi_start)
            )
            ok = False

    except OSError as exc:
        log("[ERROR] {:<28}     -- cannot read file: {}".format(path.name, exc))
        return False
    except:
        raise
    return ok


def check_data_gaps(path, cid):
    """
    Warn if gaps in B records or in valid (A) GPS fixes is found
    Returns True if clean.
    """
    ok = True
    last_b_time = None		# any B record
    last_a_time = None          # B with valid GPS data

    try:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            for raw_line in fh:
                line = raw_line.strip().upper()
                if not line:
                    continue

                if not line.startswith("B"):
                    continue

                b_time = line[1:7]

                if last_b_time is not None:
                    duration = _parse_time(b_time) - _parse_time(last_b_time)
                    if duration >= DATA_GAP_B:
                        log("[WARN]  {:<28} {:<4}-- gap in B records for {}s at {} UTC".format(
                                path.name, cid, duration, last_b_time)
                        )
                        ok = False
                last_b_time = b_time


                if line[24] == 'A':                 # valid GPS fix
                    if last_a_time is not None:
                        duration = _parse_time(b_time) - _parse_time(last_a_time)
                        if duration >= DATA_GAP_A:
                            log("[WARN]  {:<28} {:<4}-- gap in GPS fixes for {}s at {} UTC".format(
                                    path.name, cid, duration, last_a_time)
                            )
                            ok = False
                    last_a_time = b_time

        # End of file reached
        if b_time is not None and last_a_time is not None and (_parse_time(b_time) - _parse_time(last_a_time)) >= DATA_GAP_A:
            log("[WARN]  {:<28} {:<4}-- gap in GPS fixes for at {} UTC till end of file".format(
                         path.name, cid, last_a_time)
            )
            ok = False

    except OSError as exc:
        log("[ERROR] {:<28}     -- cannot read file: {}".format(path.name, exc))
        return False
    except:
        raise
    return ok


# ---------------------------------------------------------------------------
# Filename parsing
# ---------------------------------------------------------------------------

# Long format: YYYY-MM-DD-MMM-XXX-FF.IGC  (3-char serial)
#           or YYYY-MM-DD-MMM-XXXXXX-FF.IGC (6-char serial)
_LONG_RE = re.compile(
    r"^(\d{4})-(\d{2})-(\d{2})-([A-Z0-9]{3})-([A-Z0-9]{3,6})-(\d{2})\.igc$",
    re.IGNORECASE,
)

# Short format: YMDCXXXF.IGC
_SHORT_RE = re.compile(
    r"^([0-9])([1-9A-C])([1-9A-V])([A-Z0-9])([A-Z0-9]{3})([1-9A-Z])\.igc$",
    re.IGNORECASE,
)


def _decode_short_date(y_ch, m_ch, d_ch):
    year_digit = _decode_year_digit(y_ch)
    month = _decode_b36_digit(m_ch)
    day = _decode_b36_digit(d_ch)

    if year_digit is None or month is None or day is None:
        return None
    if not (1 <= month <= 12) or not (1 <= day <= 31):
        return None

    current_year = date.today().year
    candidate = current_year - (current_year % 10) + year_digit
    if candidate > current_year:
        candidate -= 10

    try:
        return date(candidate, month, day)
    except ValueError:
        return None


def parse_filename(name):
    """Decode flight date, manufacturer and serial number from an IGC filename."""

    m = _LONG_RE.match(name)
    if m:
        yyyy, mm, dd, mfr, serial, fn = m.groups()
        try:
            fdate = date(int(yyyy), int(mm), int(dd))
            if mfr[0:1].upper() == 'X':
                log(
                    "[WARN]  {:<28}     -- uncertified device ".format(name)
                )

        except ValueError:
            return None
        return FilenameInfo(
            format="long",
            fr=mfr.upper()+'-'+serial.upper(),
            flight_date=fdate,
            flight_number=int(fn),
        )

    m = _SHORT_RE.match(name)
    if m:
        y_ch, m_ch, d_ch, mfr_ch, serial, fn_ch = m.groups()
        fdate = _decode_short_date(y_ch, m_ch, d_ch)
        if fdate is None:
            return None
        fn_val = _decode_b36_digit(fn_ch)
        mfr = MANUFACTURER_CODES.get(mfr_ch.upper())

        if mfr_ch.upper() == 'X':
            log(
                "[WARN]  {:<28}     -- uncertified device ".format(name)
            )
            mfr = 'XXX'
        elif mfr is None:
            log(
                "[WARN]  {:<28}     -- unknown manufacturer code '{}' ".format(name, mfr_ch)
            )
            return None

        return FilenameInfo(
            format="short",
            fr=mfr.upper()+'-'+serial.upper(),
            flight_date=fdate,
            flight_number=fn_val or 0,
        )

    return None


# ---------------------------------------------------------------------------
# Comparison & reporting
# ---------------------------------------------------------------------------

def check_file(path):
    """Check one IGC file. Returns True if no discrepancies were found."""
    name = path.name

    fn_info = parse_filename(name)
    if fn_info is None:
        log("[SKIP]  {:<28}     -- filename does not match IGC format".format(name))
        return True

    hdr = parse_header(path)
    if hdr is None:
        return False

    ok = True

    # Uncertified devices do not have common 3-letter code, accept any
    if fn_info.format == "short" and fn_info.fr[0:3] == 'XXX':
        fn_info.fr = hdr.fr[0:3] + fn_info.fr[3:]


    # --- Serial number check ---
    if fn_info.fr != hdr.fr:
        log(
            "[WARN]  {:<28} {:<4}-- bad FR: header='{}'".format(
                name, hdr.cid, hdr.fr.lower())
        )
        ok = False

    # --- Date check ---
    if fn_info.format == "short":
        date_ok = (
            fn_info.flight_date.month == hdr.flight_date.month
            and fn_info.flight_date.day == hdr.flight_date.day
            and fn_info.flight_date.year % 10 == hdr.flight_date.year % 10
        )
        if not date_ok:
            log(
                "[WARN]  {:<28} {:<4}-- bad date: filename='{}' header='{}'".format(
                    name, hdr.cid, fn_info.flight_date, hdr.flight_date)
            )
            ok = False
    else:
        if fn_info.flight_date != hdr.flight_date:
            log(
                "[WARN]  {:<28} {:<4}-- bad date: header='{}'".format(
                    name, hdr.cid, hdr.flight_date)
            )
            ok = False

    # --- Data gap check ---
    if not check_data_gaps(path,hdr.cid):
        ok = False

    # --- Trailing data check ---
    if not check_trailing_data(path,hdr.cid):
        ok = False

    # --- Forbidden string check ---
    if not check_forbidden_strings(path,hdr.cid):
        ok = False

    # --- Blind flying check ---
    if not check_blind_flying(path, hdr.cid):
        ok = False

    if ok:
        log(
            "[OK]    {:<28} {:<4}-- date={}  serial={}".format(
                name, hdr.cid, hdr.flight_date, hdr.fr.lower())
        )

    return ok


def check_directory(directory):
    igc_files = sorted(directory.glob("*.igc")) + sorted(directory.glob("*.IGC"))
    seen = set()
    unique = []
    for p in igc_files:
        key = p.resolve()
        if key not in seen:
            seen.add(key)
            unique.append(p)

    if not unique:
        print("No IGC files found in '{}'.".format(directory))
        return

    warnings = 0
    for p in unique:
        if not check_file(p):
            warnings += 1


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def _log_path_for(target):
    """Return the log file path for a given target (file or directory)."""
    if target.is_dir():
        resolved = target.resolve()
        if resolved == Path.cwd():
            return Path("check.log")
        return Path("check_{}.log".format(resolved.name))
    else:
        parent = target.resolve().parent
        if parent == Path.cwd():
            return Path("check.log")
        return Path("check_{}.log".format(parent.name))


def main():
    global log

    targets = sys.argv[1:] if len(sys.argv) > 1 else ["."]

    for target_str in targets:
        target = Path(target_str)
        if not target.exists():
            print("ERROR: '{}' is not a file or directory.".format(target_str),
                  file=sys.stderr)
            continue

        try:
            if target.is_dir():
                lp = _log_path_for(target)
                log = Logger(lp)
                check_directory(target)
            else:
                log = Logger(None)
                check_file(target)

        finally:
            log.close()


if __name__ == "__main__":
    main()