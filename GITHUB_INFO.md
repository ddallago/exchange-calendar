# Dati da compilare per la pagina GitHub

Copia e incolla questi valori quando crei il repository.

## Creazione repository (pagina "Create a new repository")

| Campo | Valore da inserire |
|---|---|
| **Repository name** | `exchange-calendar-mcp` |
| **Description** | `Server MCP per collegare Claude al calendario Microsoft Exchange Server on-premise via EWS, in sola lettura, con autenticazione NTLM.` |
| **Visibility** | Public (o Private se vuoi tenerlo riservato) |
| **Add a README** | NO — è già incluso nel progetto |
| **Add .gitignore** | None — è già incluso |
| **Choose a license** | None — è già inclusa (MIT) |

## About (barra laterale destra del repo, icona ingranaggio)

- **Description:**
  `Server MCP per leggere il calendario di Microsoft Exchange Server on-premise (EWS) da Claude, in sola lettura, con autenticazione NTLM.`
- **Website:** (lascia vuoto)
- **Topics (tag):**
  `mcp` `model-context-protocol` `claude` `exchange` `exchange-server` `on-premise` `ews` `exchange-web-services` `calendar` `ntlm` `python` `exchangelib`

## Descrizione lunga (in cima al README, già presente)

> Server MCP che collega Claude al calendario di Microsoft Exchange tramite
> l'endpoint EWS, con autenticazione NTLM, in sola lettura.

## Primo commit (messaggio consigliato)

```
Initial commit: Exchange Calendar MCP (EWS, NTLM, sola lettura)
```

## Comandi per pubblicare (Terminale, dentro la cartella del progetto)

```bash
cd "/percorso/della/cartella/exchange_calendar"
git init
git add .
git status                 # CONTROLLA: il file .env NON deve comparire nell'elenco
git commit -m "Initial commit: Exchange Calendar MCP (EWS, NTLM, sola lettura)"
git branch -M main
git remote add origin https://github.com/<tuo-utente>/exchange-calendar-mcp.git
git push -u origin main
```

> IMPORTANTE: prima di `git commit`, esegui `git status` e verifica che **`.env`
> non sia nella lista** dei file. Se compare, fermati: significa che `.gitignore`
> non è nella cartella. Deve esserci il file `.env.example`, mai `.env`.

## Checklist sicurezza prima del push

- [ ] Il file `.env` (con la password) NON è tracciato da Git — verifica con `git status`.
- [ ] È presente `.gitignore` con la riga `.env`.
- [ ] È presente solo `.env.example` con valori di esempio (nessun dato reale).
- [ ] Nessuna password, email personale o URL aziendale nei file di esempio.
- [ ] `EXCHANGE_VERIFY_SSL=true` (verifica TLS attiva) come default.
