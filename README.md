# NovaX RP – Ticket Bot

## Instalace

1. Nainstaluj Python 3.10+
2. Nainstaluj závislosti:
   ```
   pip install -r requirements.txt
   ```
3. V souboru `bot.py` nahraď `TVUJ_BOT_TOKEN_ZDE` svým tokenem
4. Spusť bota:
   ```
   python bot.py
   ```

## Nastavení na serveru

Po spuštění bota napiš v libovolném kanálu:
```
!setup_tickets
```
Tím se pošle embed s dropdown menu do ticket kanálu.

## Hosting zdarma (Railway.app)

1. Vytvoř účet na railway.app
2. New Project → Deploy from GitHub repo
3. Přidej proměnnou prostředí: `TOKEN = tvuj_token`
4. (volitelně) uprav bot.py aby četl token z env: `TOKEN = os.getenv("TOKEN")`
