# Exchange Calendar MCP (on-premise)

Server **MCP** (Model Context Protocol) che collega Claude al calendario di
**Microsoft Exchange Server on-premise** tramite l'endpoint **EWS**
(Exchange Web Services), con autenticazione **NTLM**, in **sola lettura**.
Dopo la configurazione puoi chiedere a Claude *"che appuntamenti ho oggi?"*,
*"cosa ho la settimana prossima?"*, ecc.

> **Compatibilità:** progettato per **Exchange Server on-premise** (2013/2016/2019)
> con EWS abilitato e autenticazione **NTLM**. Non pensato per Exchange Online /
> Microsoft 365 (che usa OAuth 2.0).

> Sola lettura del calendario: il server non crea, modifica o cancella nulla.

## Strumenti esposti

- `agenda_oggi` – appuntamenti di oggi
- `prossimi_giorni` – appuntamenti dei prossimi N giorni
- `lista_appuntamenti` – appuntamenti tra due date
- `prova_connessione` – verifica credenziali ed endpoint EWS

## Requisiti

- Python 3.10 o superiore
- **Microsoft Exchange Server on-premise** (2013/2016/2019) con EWS attivo e autenticazione **NTLM**

## Installazione

```bash
git clone https://github.com/<tuo-utente>/exchange-calendar-mcp.git
cd exchange-calendar-mcp
pip install -r requirements.txt
```

## Configurazione

Copia `.env.example` in `.env` e compila i valori:

```
EXCHANGE_EWS_URL=https://mail.esempio.com/EWS/Exchange.asmx
EXCHANGE_USERNAME=DOMINIO\utente
EXCHANGE_PASSWORD=la_tua_password
EXCHANGE_EMAIL=nome.cognome@esempio.com
EXCHANGE_TIMEZONE=Europe/Rome
EXCHANGE_VERIFY_SSL=true
```

Collega il server a Claude Desktop nel file di configurazione
(`~/Library/Application Support/Claude/claude_desktop_config.json` su macOS):

```json
{
  "mcpServers": {
    "exchange-calendar": {
      "command": "python3",
      "args": ["/percorso/assoluto/exchange-calendar-mcp/server.py"]
    }
  }
}
```

Riavvia Claude Desktop e scrivi *"prova la connessione al calendario"*.

## Sicurezza

- **Nessun segreto nel repository.** Le credenziali stanno solo nel file `.env`
  locale, che è escluso da Git tramite `.gitignore`. Non caricare mai il tuo `.env`.
- **TLS attivo per default.** Il certificato del server viene verificato.
  Imposta `EXCHANGE_VERIFY_SSL=false` **solo** con certificati self-signed interni.
- **Sola lettura.** Il server non ha strumenti di scrittura sul calendario o sulla casella.
- **Permessi del file .env** (consigliato su macOS/Linux):
  ```bash
  chmod 600 .env
  ```
- Se pubblichi una tua istanza, considera l'uso di una casella/utenza dedicata
  con i soli permessi necessari.

## Risoluzione problemi

- **"Credenziali mancanti"** → `.env` assente o non compilato.
- **Errore 401** → username NTLM errato (`DOMINIO\utente`) o password sbagliata;
  prova anche con l'indirizzo email completo come username.
- **Errore certificato/SSL** → il certificato non è valido/attendibile;
  usa un certificato valido oppure, solo su reti interne fidate, `EXCHANGE_VERIFY_SSL=false`.

## Autore

Sviluppato da **Diego Dal Lago** — dev@diegodallago.it

## Licenza

MIT — vedi il file [LICENSE](LICENSE).
Copyright (c) 2026 Diego Dal Lago.
