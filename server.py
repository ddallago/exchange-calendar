#!/usr/bin/env python3
"""
MCP server that connects Claude to an ON-PREMISE Microsoft Exchange Server
calendar (2013/2016/2019) via the EWS (Exchange Web Services) endpoint.
Authentication: NTLM (Windows domain). Read-only by default, with optional
create/update/delete of calendar items when explicitly enabled.
Not intended for Exchange Online / Microsoft 365 (which uses OAuth 2.0).

Author: Diego Dal Lago <dev@diegodallago.it>
License: MIT

Credentials are read from environment variables (set in the Claude Desktop
config or in a .env file next to this script):

  EXCHANGE_EWS_URL        e.g. https://mail.example.com/EWS/Exchange.asmx
  EXCHANGE_USERNAME       e.g. DOMAIN\\user   (NTLM login)
  EXCHANGE_PASSWORD       the password
  EXCHANGE_EMAIL          e.g. name.surname@example.com  (mailbox to read)
  EXCHANGE_TIMEZONE       optional, e.g. Europe/Rome (default: Europe/Rome)
  EXCHANGE_VERIFY_SSL     optional, true=secure (default). false only for self-signed certs.
  EXCHANGE_ENABLE_WRITE   optional, false (default). true enables create/update/delete tools.
  EXCHANGE_ALLOW_INSECURE optional, false (default). true allows non-HTTPS URLs (discouraged).
"""

import os
import sys
import stat
import datetime as dt
from pathlib import Path

from mcp.server.fastmcp import FastMCP

# Load an optional .env file next to this script (handy for local testing).
# load_dotenv does NOT override variables already set in the environment,
# so the Claude Desktop config always takes precedence over .env.
_ENV_PATH = Path(__file__).with_name(".env")
try:
    from dotenv import load_dotenv
    load_dotenv(_ENV_PATH)
except Exception:
    pass

# Security warning (stderr only) if .env is readable by other users on the machine.
try:
    if os.name == "posix" and _ENV_PATH.exists():
        if _ENV_PATH.stat().st_mode & (stat.S_IRGRP | stat.S_IROTH):
            print("WARNING: the .env file is readable by other users. "
                  "Protect it with: chmod 600 .env", file=sys.stderr)
except Exception:
    pass

from exchangelib import (
    Credentials, Account, Configuration, DELEGATE, NTLM, EWSTimeZone, EWSDateTime,
    CalendarItem, Mailbox, Attendee,
)
# Meeting invitation/cancellation dispositions live in exchangelib.items.
from exchangelib.items import SEND_TO_ALL_AND_SAVE_COPY, SEND_TO_NONE

# TLS certificate verification: ON by default (secure behaviour).
# Disable it ONLY if your Exchange uses an internal self-signed certificate,
# by setting EXCHANGE_VERIFY_SSL=false in the .env file.
if os.environ.get("EXCHANGE_VERIFY_SSL", "true").strip().lower() in ("false", "0", "no"):
    import urllib3
    from exchangelib.protocol import BaseProtocol, NoVerifyHTTPAdapter
    BaseProtocol.HTTP_ADAPTER_CLS = NoVerifyHTTPAdapter
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


mcp = FastMCP("exchange-calendar")

_ACCOUNT = None  # cached connection

# Write switch: the create/update/delete tools are registered ONLY when
# EXCHANGE_ENABLE_WRITE=true in the .env file. The server is read-only by default.
WRITE_ENABLED = os.environ.get("EXCHANGE_ENABLE_WRITE", "false").strip().lower() in ("true", "1", "yes")


def _tz():
    """Return the configured timezone (defaults to Europe/Rome)."""
    name = os.environ.get("EXCHANGE_TIMEZONE", "Europe/Rome")
    try:
        return EWSTimeZone(name)
    except Exception:
        return EWSTimeZone("Europe/Rome")


def _get_account():
    """Create the Exchange account connection once and cache it."""
    global _ACCOUNT
    if _ACCOUNT is not None:
        return _ACCOUNT

    url = os.environ.get("EXCHANGE_EWS_URL")
    user = os.environ.get("EXCHANGE_USERNAME")
    pwd = os.environ.get("EXCHANGE_PASSWORD")
    email = os.environ.get("EXCHANGE_EMAIL")

    missing = [k for k, v in {
        "EXCHANGE_EWS_URL": url,
        "EXCHANGE_USERNAME": user,
        "EXCHANGE_PASSWORD": pwd,
        "EXCHANGE_EMAIL": email,
    }.items() if not v]
    if missing:
        raise RuntimeError(
            "Missing credentials: " + ", ".join(missing) +
            ". Set them in the Claude Desktop config or in the .env file."
        )

    # HTTPS is required: over http the NTLM credentials would travel in clear text.
    if not url.lower().startswith("https://"):
        if os.environ.get("EXCHANGE_ALLOW_INSECURE", "false").strip().lower() not in ("true", "1", "yes"):
            raise RuntimeError(
                "EXCHANGE_EWS_URL must use https:// : over http the NTLM credentials "
                "travel in clear text. To force it (discouraged) set EXCHANGE_ALLOW_INSECURE=true."
            )

    creds = Credentials(username=user, password=pwd)
    config = Configuration(
        service_endpoint=url,
        credentials=creds,
        auth_type=NTLM,
    )
    _ACCOUNT = Account(
        primary_smtp_address=email,
        config=config,
        access_type=DELEGATE,
        autodiscover=False,
    )
    return _ACCOUNT


def _parse_date(value: str) -> dt.date:
    """Accept 'YYYY-MM-DD', or 'today'/'oggi', 'tomorrow'/'domani'."""
    value = (value or "").strip().lower()
    if value in ("", "today", "oggi"):
        return dt.date.today()
    if value in ("tomorrow", "domani"):
        return dt.date.today() + dt.timedelta(days=1)
    return dt.datetime.strptime(value, "%Y-%m-%d").date()


def _parse_datetime(value: str) -> EWSDateTime:
    """Parse 'YYYY-MM-DD HH:MM' into a timezone-aware EWSDateTime."""
    d = dt.datetime.strptime((value or "").strip(), "%Y-%m-%d %H:%M")
    return EWSDateTime(d.year, d.month, d.day, d.hour, d.minute, 0, tzinfo=_tz())


def _format_events(items, show_id=False) -> str:
    """Format calendar items into a readable list."""
    rows = []
    for it in items:
        start = it.start
        end = it.end
        try:
            start = start.astimezone(_tz())
            end = end.astimezone(_tz())
        except Exception:
            pass
        s = start.strftime("%Y-%m-%d %H:%M") if hasattr(start, "strftime") else str(start)
        e = end.strftime("%H:%M") if hasattr(end, "strftime") else str(end)
        subject = it.subject or "(no title)"
        location = f" @ {it.location}" if getattr(it, "location", None) else ""
        organizer = ""
        try:
            if it.organizer and it.organizer.name:
                organizer = f" - org.: {it.organizer.name}"
        except Exception:
            pass
        row = f"- {s}-{e}  {subject}{location}{organizer}"
        if show_id:
            row += f"  [id: {it.id}]"
        rows.append(row)
    if not rows:
        return "No appointments in the requested period."
    return "\n".join(rows)


@mcp.tool()
def list_appointments(start_date: str = "today", end_date: str = "") -> str:
    """
    List calendar appointments between two dates (inclusive).
    start_date / end_date in YYYY-MM-DD format (or 'today'/'tomorrow').
    If end_date is empty, the same day as start_date is used.
    """
    account = _get_account()
    tz = _tz()
    d0 = _parse_date(start_date)
    d1 = _parse_date(end_date) if end_date else d0
    if d1 < d0:
        raise ValueError("end_date is earlier than start_date.")
    if (d1 - d0).days > 366:
        raise ValueError("Range too large: 366 days maximum.")
    start = EWSDateTime(d0.year, d0.month, d0.day, 0, 0, 0, tzinfo=tz)
    end = EWSDateTime(d1.year, d1.month, d1.day, 23, 59, 59, tzinfo=tz)
    items = account.calendar.view(start=start, end=end).order_by("start")
    header = f"Appointments from {d0.isoformat()} to {d1.isoformat()}:\n"
    return header + _format_events(items, show_id=WRITE_ENABLED)


@mcp.tool()
def today_agenda() -> str:
    """Show today's appointments."""
    return list_appointments("today", "today")


@mcp.tool()
def next_days(days: int = 7) -> str:
    """Show appointments for the next N days (default 7, max 366)."""
    days = max(1, min(int(days), 366))
    d0 = dt.date.today()
    d1 = d0 + dt.timedelta(days=days)
    return list_appointments(d0.isoformat(), d1.isoformat())


@mcp.tool()
def test_connection() -> str:
    """Check that the credentials and the EWS endpoint work."""
    account = _get_account()
    try:
        n = account.calendar.total_count
        mode = "read/write" if WRITE_ENABLED else "read-only"
        return f"OK: connected to {account.primary_smtp_address} ({mode}). Calendar items: {n}."
    except Exception as ex:
        return f"Connected but error reading the calendar: {str(ex)[:200]}"


# --- Write tools (create / update / delete) ---------------------------------
# Registered ONLY when EXCHANGE_ENABLE_WRITE=true. Deletion moves the item to the
# Deleted Items folder (recoverable) and sends cancellations to any attendees.

def _parse_attendees(attendees: str):
    """Turn a comma/semicolon separated string of emails into Attendee objects."""
    emails = [e.strip() for e in (attendees or "").replace(";", ",").split(",") if e.strip()]
    return [Attendee(mailbox=Mailbox(email_address=e)) for e in emails]


def create_appointment(title: str, start: str, end: str,
                       location: str = "", description: str = "", attendees: str = "") -> str:
    """
    Create a new calendar appointment.
    start / end in 'YYYY-MM-DD HH:MM' format. attendees = comma-separated emails
    (an invitation email is sent to the attendees, if any).
    """
    account = _get_account()
    item = CalendarItem(
        account=account,
        folder=account.calendar,
        subject=title,
        start=_parse_datetime(start),
        end=_parse_datetime(end),
        location=(location or None),
        body=(description or None),
    )
    attendee_objs = _parse_attendees(attendees)
    if attendee_objs:
        item.required_attendees = attendee_objs
    send = SEND_TO_ALL_AND_SAVE_COPY if attendee_objs else SEND_TO_NONE
    item.save(send_meeting_invitations=send)
    return f"Created: '{title}' ({start} -> {end}). [id: {item.id}]"


def update_appointment(event_id: str, title: str = "", start: str = "",
                       end: str = "", location: str = "", description: str = "") -> str:
    """
    Update an existing appointment identified by event_id (the [id: ...] shown in the list).
    Only the non-empty fields are changed. If the event has attendees, they receive an update email.
    """
    account = _get_account()
    item = account.calendar.get(id=event_id)
    fields = []
    if title:
        item.subject = title; fields.append("subject")
    if start:
        item.start = _parse_datetime(start); fields.append("start")
    if end:
        item.end = _parse_datetime(end); fields.append("end")
    if location:
        item.location = location; fields.append("location")
    if description:
        item.body = description; fields.append("body")
    if not fields:
        return "Nothing to update: provide at least one field."
    send = SEND_TO_ALL_AND_SAVE_COPY if getattr(item, "required_attendees", None) else SEND_TO_NONE
    item.save(update_fields=fields, send_meeting_invitations=send)
    return f"Updated ({', '.join(fields)}). [id: {item.id}]"


def delete_appointment(event_id: str) -> str:
    """
    Delete an appointment identified by event_id. The item is moved to the
    Deleted Items folder (recoverable). Cancellations are sent to any attendees.
    """
    account = _get_account()
    item = account.calendar.get(id=event_id)
    subject = item.subject or "(no title)"
    send = SEND_TO_ALL_AND_SAVE_COPY if getattr(item, "required_attendees", None) else SEND_TO_NONE
    item.move_to_trash(send_meeting_cancellations=send)
    return f"Moved to Deleted Items (recoverable): '{subject}'."


# Register the write tools only when explicitly enabled.
if WRITE_ENABLED:
    create_appointment = mcp.tool()(create_appointment)
    update_appointment = mcp.tool()(update_appointment)
    delete_appointment = mcp.tool()(delete_appointment)


if __name__ == "__main__":
    mcp.run()
