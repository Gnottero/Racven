# Turn Piatts

Webapp locale per la gestione del turno piatti e la bacheca messaggi di una comunità studentesca, pensata per girare su un Raspberry Pi collegato a una TV.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

export FLASK_APP=racven.py
cp .env.example .env   # poi modifica SECRET_KEY

flask init-db
flask create-admin
```

## Sviluppo

```bash
flask run --debug
```

`racven.py` esegue `app.run(..., threaded=True)`: il threading è necessario perché l'endpoint SSE (`/tv/stream`) tiene una connessione aperta indefinitamente e bloccherebbe le altre richieste sul server di sviluppo altrimenti.

## Esecuzione "in produzione" (Raspberry Pi)

```bash
waitress-serve --host=0.0.0.0 --port=8080 racven:app
```

`waitress` è un server WSGI puro Python, leggero e affidabile su Raspberry Pi, e gestisce correttamente la connessione SSE lunga della pagina TV.

## Pagine principali

- `/login`, `/register/` — autenticazione.
- `/` — pagina principale: invio messaggi alla TV e pulsante per mostrare il turno piatti.
- `/admin` — dashboard admin: elenco utenti, toggle stato contributore.
- `/tv` — pagina kiosk da aprire a schermo intero sulla TV (**non richiede login**: è pensata per un dispositivo fisico condiviso su rete locale attendibile, non per l'accesso remoto).

## Kiosk su Raspberry Pi

Raspberry Pi OS (specie la variante *Lite*) può non includere di default alcun font emoji a colori: senza installarne uno, le emoji nei messaggi vengono mostrate come riquadri vuoti sulla TV. Installa il font prima di avviare il kiosk:

```bash
sudo apt install -y fonts-noto-color-emoji
fc-cache -f
```

Per mostrare `/tv` a schermo intero via Chromium, e permettere il suono di notifica di partire senza interazione utente:

```bash
chromium-browser --kiosk --autoplay-policy=no-user-gesture-required http://localhost:8080/tv
```

## Note

- Il database è SQLite (`database.db` nella root del progetto), niente ORM: le query sono in `database/*_dao.py`.
- Il turno piatti viene ricalcolato in modo "lazy" (al primo accesso del mese, o quando un admin cambia lo stato contributore di qualcuno) — non serve nessuno scheduler esterno.
- I font (DM Sans / DM Mono) sono salvati localmente in `static/fonts/`: l'app funziona anche senza connessione internet.
- La protezione CSRF è implementata "a mano" tramite token di sessione (vedi `csrf.py`), senza dipendenze aggiuntive.
