# Exchange Calendar MCP (on-premise)

*[Versione italiana: README.it.md](README.it.md)*

An **MCP** (Model Context Protocol) server that connects Claude to an
**on-premise Microsoft Exchange Server** calendar via the **EWS**
(Exchange Web Services) endpoint, using **NTLM** authentication.
**Read-only** by default; it can optionally **create, update and delete** appointments.

> **Compatibility:** designed for **on-premise Exchange Server** (2013/2016/2019)
> with EWS enabled and **NTLM** authentication. Not intended for Exchange Online /
> Microsoft 365 (which uses OAuth 2.0).

## Tools

Read-only (always available):
- `today_agenda` – today's appointments
- `next_days` – appointments for the next N days
- `list_appointments` – appointments between two dates
- `test_connection` – check credentials and the EWS endpoint

Write (only when `EXCHANGE_ENABLE_WRITE=true`):
- `create_appointment` – create a new appointment (optionally with attendees)
- `update_appointment` – update an existing appointment
- `delete_appointment` – move an appointment to the Deleted Items folder (recoverable)

## Requirements

- Python 3.10 or newer
- **On-premise Microsoft Exchange Server** (2013/2016/2019) with EWS enabled and **NTLM** authentication

## Installation

```bash
git clone https://github.com/<your-user>/exchange-calendar-mcp.git
cd exchange-calendar-mcp
pip install -r requirements.txt
```

## Configuration

1. Copy the **`env.example`** file and rename it to **`.env`** — that is, **add a dot
   at the start of the name**. The leading dot makes it the hidden config file the
   script actually reads.

   ```bash
   cp env.example .env
   ```

2. Open `.env` and fill in the values:

   ```
   EXCHANGE_EWS_URL=https://mail.example.com/EWS/Exchange.asmx
   EXCHANGE_USERNAME=DOMAIN\user
   EXCHANGE_PASSWORD=your_password
   EXCHANGE_EMAIL=name.surname@example.com
   EXCHANGE_TIMEZONE=Europe/Rome
   EXCHANGE_VERIFY_SSL=true
   EXCHANGE_ENABLE_WRITE=false
   ```

3. Register the server in the Claude Desktop config file
   (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

   ```json
   {
     "mcpServers": {
       "exchange-calendar": {
         "command": "python3",
         "args": ["/absolute/path/exchange-calendar-mcp/server.py"]
       }
     }
   }
   ```

4. Restart Claude Desktop and type *"test the calendar connection"*.

## Enabling write access (create / update / delete)

The server is **read-only** by default. To enable the commands that modify the
calendar, set in `.env`:

```
EXCHANGE_ENABLE_WRITE=true
```

then restart Claude Desktop. Behaviour:

- **Delete = Deleted Items.** Deleted appointments are moved to the "Deleted Items"
  folder and are **recoverable**, not permanently erased.
- **Invitations.** When you create or update an appointment with attendees, an
  invitation/update email is sent to them; deletions send a cancellation.
- To go back to read-only, set `EXCHANGE_ENABLE_WRITE=false` again.

## Security

- **No secrets in the repository.** Credentials live only in the local `.env` file,
  which is Git-ignored. Never commit your `.env`; only `env.example` goes on GitHub.
- **TLS on by default.** The server certificate is verified.
  Set `EXCHANGE_VERIFY_SSL=false` **only** for internal self-signed certificates.
- **HTTPS required.** The server rejects `http://` endpoints so NTLM credentials
  never travel in clear text (discouraged override: `EXCHANGE_ALLOW_INSECURE=true`).
- **Write disabled by default.** The calendar-modifying commands exist only with
  `EXCHANGE_ENABLE_WRITE=true`.
- **Input limits.** Maximum query range of 366 days.
- **.env permissions** (recommended on macOS/Linux):
  ```bash
  chmod 600 .env
  ```

## Troubleshooting

- **"Missing credentials"** → `.env` missing or empty (remember the leading dot).
- **401 error** → wrong NTLM username (`DOMAIN\user`) or password; try the full
  email address as the username.
- **create/update/delete tools not showing** → `EXCHANGE_ENABLE_WRITE=true` is missing in `.env`.

## Author

Developed by **Diego Dal Lago** — dev@diegodallago.it

## License

MIT — see the [LICENSE](LICENSE) file.
Copyright (c) 2026 Diego Dal Lago.
