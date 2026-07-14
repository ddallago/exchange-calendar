# Exchange Calendar MCP (on-premise)

*[English version (main): README.md](README.md)*

Server **MCP** (Model Context Protocol) che collega Claude al calendario di
**Microsoft Exchange Server on-premise** tramite l'endpoint **EWS**
(Exchange Web Services), con autenticazione **NTLM**. In **sola lettura** per
default; opzionalmente può **creare, modificare e cancellare** appuntamenti.

> **Compatibilità:** progettato per **Exchange Server on-premise** (2013/2016/2019)
> con EWS abilitato e autenticazione **NTLM**. Non pensato per Exchange Online /
> Microsoft 365 (che usa OAuth 2.0).

## Strumenti esposti

Sola lettura (sempre attivi):
- `today_agenda` – appuntamenti di oggi
- `next_days` – appuntamenti dei prossimi N giorni
- `list_appointments` – appuntamenti tra due date
- `test_connection` – verifica credenziali ed endpoint EWS

Scrittura (attivi solo con `EXCHANGE_ENABLE_WRITE=true`):
- `create_appointment` – crea un nuovo appuntamento (con eventuali invitati)
- `update_appointment` – modifica un appuntamento esistente
- `delete_appointment` – sposta un appuntamento nel Cestino (recuperabile)

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

1. Copia il file **`env.example`** e rinominalo in **`.env`** — cioè **aggiungi un punto
   all'inizio del nome**. Il punto iniziale rende il file la configurazione nascosta
   che lo script legge davvero.

   ```bash
   cp env.example .env
   ```

2. Apri `.env` e compila i valori:

   ```
   EXCHANGE_EWS_URL=https://mail.esempio.com/EWS/Exchange.asmx
   EXCHANGE_USERNAME=DOMINIO\utente
   EXCHANGE_PASSWORD=la_tua_password
   EXCHANGE_EMAIL=nome.cognome@esempio.com
   EXCHANGE_TIMEZONE=Europe/Rome
   EXCHANGE_VERIFY_SSL=true
   EXCHANGE_ENABLE_WRITE=false
   ```

3. Collega il server a Claude Desktop nel file di configurazione
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

4. Riavvia Claude Desktop e scrivi *"prova la connessione al calendario"*.

## Abilitare la scrittura (crea / modifica / cancella)

Per default il server è in **sola lettura**. Per abilitare i comandi che modificano
il calendario, imposta nel `.env`:

```
EXCHANGE_ENABLE_WRITE=true
```

e riavvia Claude Desktop. Comportamento:

- **Cancellazione = Cestino.** Gli appuntamenti cancellati vengono spostati nella
  cartella "Posta eliminata" e sono **recuperabili**, non eliminati definitivamente.
- **Inviti.** Quando crei o modifichi un appuntamento con partecipanti, viene inviata
  loro l'email di invito/aggiornamento; le cancellazioni inviano l'annullamento.
- Per tornare in sola lettura basta rimettere `EXCHANGE_ENABLE_WRITE=false`.

## Sicurezza

- **Nessun segreto nel repository.** Le credenziali stanno solo nel file `.env`
  locale, escluso da Git. Non caricare mai il tuo `.env`; su GitHub va solo `env.example`.
- **TLS attivo per default.** Il certificato del server viene verificato.
  Imposta `EXCHANGE_VERIFY_SSL=false` **solo** con certificati self-signed interni.
- **HTTPS obbligatorio.** Il server rifiuta endpoint `http://` per non esporre le
  credenziali NTLM in chiaro (override sconsigliato: `EXCHANGE_ALLOW_INSECURE=true`).
- **Scrittura disattivata per default.** I comandi che modificano il calendario
  esistono solo con `EXCHANGE_ENABLE_WRITE=true`.
- **Limiti sugli input.** Intervallo massimo di 366 giorni per interrogazione.
- **Permessi del file .env** (consigliato su macOS/Linux):
  ```bash
  chmod 600 .env
  ```

## Risoluzione problemi

- **"Missing credentials"** → `.env` assente o non compilato (ricorda il punto iniziale).
- **Errore 401** → username NTLM errato (`DOMINIO\utente`) o password sbagliata;
  prova anche con l'indirizzo email completo come username.
- **I comandi crea/modifica/cancella non compaiono** → manca `EXCHANGE_ENABLE_WRITE=true` nel `.env`.

## Autore

Sviluppato da **Diego Dal Lago** — dev@diegodallago.it

## Licenza

MIT — vedi il file [LICENSE](LICENSE).
Copyright (c) 2026 Diego Dal Lago.
