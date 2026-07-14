#!/usr/bin/env python3
"""
Server MCP che collega Claude al calendario di Microsoft Exchange Server ON-PREMISE
(2013/2016/2019) tramite l'endpoint EWS (Exchange Web Services).
Autenticazione: NTLM (dominio Windows). Sola lettura del proprio calendario.
Non pensato per Exchange Online / Microsoft 365 (che usa OAuth 2.0).

Autore: Diego Dal Lago <dev@diegodallago.it>
Licenza: MIT

Credenziali lette dalle variabili d'ambiente (impostate nella config di Claude Desktop
o in un file .env accanto a questo script):

  EXCHANGE_EWS_URL   es. https://mail.esempio.com/EWS/Exchange.asmx
  EXCHANGE_USERNAME  es. DOMINIO\\utente   (login NTLM)
  EXCHANGE_PASSWORD  la password
  EXCHANGE_EMAIL     es. nome.cognome@esempio.com  (casella da leggere)
  EXCHANGE_TIMEZONE  opzionale, es. Europe/Rome (default: Europe/Rome)
  EXCHANGE_VERIFY_SSL opzionale, true=sicuro (default). false solo per certificati self-signed.
"""

import os
import datetime as dt
from pathlib import Path

from mcp.server.fastmcp import FastMCP

# Carica un eventuale file .env accanto allo script (comodo per i test)
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).with_name(".env"))
except Exception:
    pass

from exchangelib import (
    Credentials, Account, Configuration, DELEGATE, NTLM, EWSTimeZone, EWSDateTime,
)

# Verifica del certificato TLS: ATTIVA per default (comportamento sicuro).
# Disattivala SOLO se il tuo Exchange usa un certificato self-signed interno,
# impostando EXCHANGE_VERIFY_SSL=false nel file .env.
if os.environ.get("EXCHANGE_VERIFY_SSL", "true").strip().lower() in ("false", "0", "no"):
    import urllib3
    from exchangelib.protocol import BaseProtocol, NoVerifyHTTPAdapter
    BaseProtocol.HTTP_ADAPTER_CLS = NoVerifyHTTPAdapter
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


mcp = FastMCP("exchange-calendar")

_ACCOUNT = None  # cache della connessione


def _tz():
    name = os.environ.get("EXCHANGE_TIMEZONE", "Europe/Rome")
    try:
        return EWSTimeZone(name)
    except Exception:
        return EWSTimeZone("Europe/Rome")


def _get_account():
    """Crea (una volta sola) la connessione all'account Exchange."""
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
            "Credenziali mancanti: " + ", ".join(missing) +
            ". Impostale nella config di Claude Desktop o nel file .env."
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
    """Accetta 'YYYY-MM-DD' oppure 'oggi'/'today'."""
    value = (value or "").strip().lower()
    if value in ("", "oggi", "today"):
        return dt.date.today()
    if value in ("domani", "tomorrow"):
        return dt.date.today() + dt.timedelta(days=1)
    return dt.datetime.strptime(value, "%Y-%m-%d").date()


def _fmt_events(items) -> str:
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
        subject = it.subject or "(senza titolo)"
        location = f" @ {it.location}" if getattr(it, "location", None) else ""
        organizer = ""
        try:
            if it.organizer and it.organizer.name:
                organizer = f" — org.: {it.organizer.name}"
        except Exception:
            pass
        rows.append(f"• {s}-{e}  {subject}{location}{organizer}")
    if not rows:
        return "Nessun appuntamento nel periodo richiesto."
    return "\n".join(rows)


@mcp.tool()
def lista_appuntamenti(data_inizio: str = "oggi", data_fine: str = "") -> str:
    """
    Elenca gli appuntamenti del calendario tra due date (incluse).
    data_inizio / data_fine nel formato YYYY-MM-DD (oppure 'oggi'/'domani').
    Se data_fine e' vuota, usa lo stesso giorno di data_inizio.
    """
    account = _get_account()
    tz = _tz()
    d0 = _parse_date(data_inizio)
    d1 = _parse_date(data_fine) if data_fine else d0
    start = EWSDateTime(d0.year, d0.month, d0.day, 0, 0, 0, tzinfo=tz)
    end = EWSDateTime(d1.year, d1.month, d1.day, 23, 59, 59, tzinfo=tz)
    items = account.calendar.view(start=start, end=end).order_by("start")
    header = f"Appuntamenti dal {d0.isoformat()} al {d1.isoformat()}:\n"
    return header + _fmt_events(items)


@mcp.tool()
def agenda_oggi() -> str:
    """Mostra gli appuntamenti di oggi."""
    return lista_appuntamenti("oggi", "oggi")


@mcp.tool()
def prossimi_giorni(giorni: int = 7) -> str:
    """Mostra gli appuntamenti dei prossimi N giorni (default 7)."""
    d0 = dt.date.today()
    d1 = d0 + dt.timedelta(days=max(1, giorni))
    return lista_appuntamenti(d0.isoformat(), d1.isoformat())


@mcp.tool()
def prova_connessione() -> str:
    """Verifica che le credenziali e l'endpoint EWS funzionino."""
    account = _get_account()
    try:
        n = account.calendar.total_count
        return f"OK: connesso a {account.primary_smtp_address}. Elementi nel calendario: {n}."
    except Exception as ex:
        return f"Connesso ma errore leggendo il calendario: {ex}"


if __name__ == "__main__":
    mcp.run()
