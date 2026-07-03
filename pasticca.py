import json
import time
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
import requests

# -------------------------------------------------------------
# CONFIGURATION
# -------------------------------------------------------------
# Replace with your actual Telegram Bot Token from @BotFather
BOT_TOKEN = "8221208999:AAE52kQ-ouyyFMPv6D0JqMFChMqdG_UWt2c"
# Replace with your actual External API URL
EXTERNAL_API_URL = "https://api.telegram.org/bot{BOT_TOKEN}"

BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

ADMIN_ID = 8901052436

# Dictionary to track the conversation state for each chat
# States: None (default), 'AWAITING_PHONE'
USER_STATES = {}

# -------------------------------------------------------------
# TELEGRAM BOT API FUNCTIONS
# -------------------------------------------------------------
def send_message(chat_id, text, reply_markup=None):
    """Sends a message to a specific chat using the sendMessage API endpoint."""
    url = f"{BASE_URL}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML"
    }
    if reply_markup:
        payload["reply_markup"] = json.dumps(reply_markup)
        
    try:
        response = requests.post(url, json=payload)
        return response.json()
    except Exception as e:
        print(f"Error sending message: {e}")
        return None

def handle_updates(updates):
    """Processes a batch of incoming updates from Telegram."""
    for update in updates:
        # Ignore updates that don't contain a text message
        if "message" not in update or "text" not in update["message"]:
            continue
            
        message = update["message"]
        chat_id = message["chat"]["id"]
        text = message["text"].strip()
        
        # 1. Handle /start command
        if text == "/start":
            USER_STATES[chat_id] = None  # Reset state
            welcome_text = "Welcome! Click the button below to lookup a phone number."
            
            # Custom reply keyboard structure
            keyboard = {
                "keyboard": [[{"text": "📱 Phone Lookup"}]],
                "resize_keyboard": True,
                "one_time_keyboard": False
            }
            send_message(chat_id, welcome_text, reply_markup=keyboard)
            
        # 2. Handle "📱 Phone Lookup" button press
        elif text == "📱 Phone Lookup":
            USER_STATES[chat_id] = 'AWAITING_PHONE'
            send_message(chat_id, "📞 Scrivi un numero di telefono:")
            
        # 3. Process expected phone number input
        elif USER_STATES.get(chat_id) == 'AWAITING_PHONE':
            # Check if input is exactly a 10-digit number
            if text.isdigit() and len(text) == 10:
                send_message(chat_id, "⏳ Fetching data from the API...")
                
                try:
                    # Append the phone number as a query parameter (adjust as needed for your specific API)
                    response = requests.get(EXTERNAL_API_URL, params={"phone": text}, timeout=10)
                    
                    try:
                        api_json = response.json()
                        # Indent JSON by 2 spaces for beautiful HTML rendering
                        formatted_json = json.dumps(api_json, indent=2)
                    except ValueError:
                        # Fallback case if the external API returns raw text instead of valid JSON
                        formatted_json = json.dumps({"raw_response": response.text}, indent=2)
                        
                    # Wrap JSON inside <pre> tag for preformatted structure in Telegram
                    response_msg = f"<pre>{formatted_json}</pre>"
                    send_message(chat_id, response_msg)
                    
                except Exception as e:
                    send_message(chat_id, f"❌ Error contacting external API: {str(e)}")
                
                # Reset conversation state back to default after processing
                USER_STATES[chat_id] = None
            else:
                # Error handling for invalid inputs
                send_message(chat_id, "⚠️ Error: Please provide a valid 10-digit numeric mobile number.")
                
        # 4. Handle unexpected text inputs
        else:
            send_message(chat_id, "Please use the menu button or type /start to interact with the bot.")

def bot_polling_loop():
    """Main long polling loop using manual offset-based getUpdates."""
    offset = None
    print("Bot polling engine started...")
    
    while True:
        # Safety guard clause: don't bombard Telegram if token hasn't been set yet
        if not BOT_TOKEN:
            print("Configuration Error: BOT_TOKEN variable is empty. Please set it.")
            time.sleep(5)
            continue
            
        url = f"{BASE_URL}/getUpdates"
        params = {"timeout": 30}  # Server-side long polling delay
        if offset:
            params["offset"] = offset
            
        try:
            response = requests.get(url, params=params, timeout=35)
            if response.status_code == 200:
                data = response.json()
                if data.get("ok"):
                    updates = data.get("result", [])
                    if updates:
                        handle_updates(updates)
                        # Offset must be greater than the highest update_id received to acknowledge them
                        offset = updates[-1]["update_id"] + 1
            else:
                print(f"Telegram API Error: Status code {response.status_code}")
        except Exception as e:
            print(f"Network error during polling: {e}")
            
        # Short cooldown to prevent high CPU utilization on loop errors
        time.sleep(1)

# -------------------------------------------------------------
# DUMMY HTTP SERVER
# -------------------------------------------------------------
class DummyHTTPServerHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Standard health-check style response for incoming GET requests."""
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(b"<html><body><h1>Bot Dummy HTTP Server is Running!</h1></body></html>")

    def log_message(self, format, *args):
        # Override to silence standard console log flooding
        return

def run_dummy_server(port=8080):
    """Starts the dummy web server on the specified port configuration."""
    server_address = ('', port)
    httpd = HTTPServer(server_address, DummyHTTPServerHandler)
    print(f"Dummy HTTP server actively listening on port {port}...")
    httpd.serve_forever()

# -------------------------------------------------------------
# ENTRYPOINT
# -------------------------------------------------------------
if __name__ == "__main__":
    # Launch the dummy HTTP server context in a daemonized background thread
    server_thread = threading.Thread(target=run_dummy_server, kwargs={'port': 8080}, daemon=True)
    server_thread.start()
    
    # Run the Telegram polling cycle sequentially on the main thread
    try:
        bot_polling_loop()
    except KeyboardInterrupt:
        print("\nProcess terminated gracefully by user.")
import json
import time
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
import requests

# -------------------------------------------------------------
# CONFIGURAZIONE
# -------------------------------------------------------------
# Inserisci qui il Token del tuo Bot Telegram preso da @BotFather
BOT_TOKEN = "8221208999:AAE52kQ-ouyyFMPv6D0JqMFChMqdG_UWt2c"
# Inserisci qui l'URL dell'API esterna per la ricerca
EXTERNAL_API_URL = ""

BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

# Dizionario per gestire lo stato della conversazione per ogni utente
# Stati possibili: None (default), 'AWAITING_PHONE', 'AWAITING_USERNAME'
USER_STATES = {}

# -------------------------------------------------------------
# FUNZIONI API DI TELEGRAM
# -------------------------------------------------------------
def send_message(chat_id, text, reply_markup=None):
    """Invia un messaggio a una chat specifica usando l'endpoint sendMessage."""
    url = f"{BASE_URL}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML"
    }
    if reply_markup:
        payload["reply_markup"] = json.dumps(reply_markup)
        
    try:
        response = requests.post(url, json=payload)
        return response.json()
    except Exception as e:
        print(f"Errore nell'invio del messaggio: {e}")
        return None

def handle_updates(updates):
    """Elabora i messaggi in entrata ricevuti da Telegram."""
    for update in updates:
        if "message" not in update or "text" not in update["message"]:
            continue
            
        message = update["message"]
        chat_id = message["chat"]["id"]
        text = message["text"].strip()
        
        # 1. Gestione comando /start
        if text == "/start":
            USER_STATES[chat_id] = None  # Reset dello stato
            welcome_text = "Benvenuto! Scegli un'opzione dalla tastiera in basso per iniziare la ricerca."
            
            # Tastiera personalizzata con entrambi i pulsanti richiesti
            keyboard = {
                "keyboard": [
                    [{"text": "📱 Phone Lookup"}, {"text": "🔎 username"}]
                ],
                "resize_keyboard": True,
                "one_time_keyboard": False
            }
            send_message(chat_id, welcome_text, reply_markup=keyboard)
            
        # 2. Gestione pressione del pulsante "📱 Phone Lookup"
        elif text == "📱 Phone Lookup":
            USER_STATES[chat_id] = 'AWAITING_PHONE'
            send_message(chat_id, "📞 Scrivi un numero di telefono:")
            
        # 3. Gestione pressione del pulsante "🔎 username"
        elif text == "🔎 username":
            USER_STATES[chat_id] = 'AWAITING_USERNAME'
            send_message(chat_id, "🔎 Scrivi un username:")
            
        # 4. Stato: Attesa Numero di Telefono (10 cifre)
        elif USER_STATES.get(chat_id) == 'AWAITING_PHONE':
            if text.isdigit() and len(text) == 10:
                send_message(chat_id, "⏳ Ricerca del numero in corso...")
                try:
                    # Chiamata API per il telefono
                    response = requests.get(EXTERNAL_API_URL, params={"phone": text}, timeout=10)
                    try:
                        api_json = response.json()
                        formatted_json = json.dumps(api_json, indent=2)
                    except ValueError:
                        formatted_json = json.dumps({"raw_response": response.text}, indent=2)
                        
                    send_message(chat_id, f"<pre>{formatted_json}</pre>")
                except Exception as e:
                    send_message(chat_id, f"❌ Errore API esterna: {str(e)}")
                
                USER_STATES[chat_id] = None  # Reset dello stato
            else:
                send_message(chat_id, "⚠️ Errore: Inserisci un numero di telefono valido di esattamente 10 cifre numeriche.")
                
        # 5. Stato: Attesa Username (Rileva ed elimina l'eventuale @)
        elif USER_STATES.get(chat_id) == 'AWAITING_USERNAME':
            # Rimuove la @ se l'utente l'ha scritta (es. @username -> username)
            username_pulito = text.lstrip('@')
            
            if len(username_pulito) >= 3:
                send_message(chat_id, f"⏳ Ricerca dell'account @{username_pulito} in corso...")
                try:
                    # Chiamata API per l'username
                    response = requests.get(EXTERNAL_API_URL, params={"username": username_pulito}, timeout=10)
                    try:
                        api_json = response.json()
                        formatted_json = json.dumps(api_json, indent=2)
                    except ValueError:
                        formatted_json = json.dumps({"raw_response": response.text}, indent=2)
                        
                    send_message(chat_id, f"<pre>{formatted_json}</pre>")
                except Exception as e:
                    send_message(chat_id, f"❌ Errore API esterna: {str(e)}")
                
                USER_STATES[chat_id] = None  # Reset dello stato
            else:
                send_message(chat_id, "⚠️ Username troppo corto o non valido. Riprova.")
                
        # 6. Risposta standard di fallback
        else:
            send_message(chat_id, "Usa i pulsanti della tastiera o digita /start per iniziare.")

def bot_polling_loop():
    """Ciclo principale di long polling basato su offset."""
    offset = None
    print("Loop di polling unificato del Bot avviato...")
    
    while True:
        if not BOT_TOKEN:
            print("Errore: La variabile BOT_TOKEN è vuota. Configurala per avviare il bot.")
            time.sleep(5)
            continue
            
        url = f"{BASE_URL}/getUpdates"
        params = {"timeout": 30}
        if offset:
            params["offset"] = offset
            
        try:
            response = requests.get(url, params=params, timeout=35)
            if response.status_code == 200:
                data = response.json()
                if data.get("ok"):
                    updates = data.get("result", [])
                    if updates:
                        handle_updates(updates)
                        offset = updates[-1]["update_id"] + 1
            else:
                print(f"Errore API Telegram: Status code {response.status_code}")
        except Exception as e:
            print(f"Errore di rete durante il polling: {e}")
            
        time.sleep(1)

# -------------------------------------------------------------
# DUMMY HTTP SERVER DI SFONDO
# -------------------------------------------------------------
class DummyHTTPServerHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(b"<html><body><h1>Bot Lookup OSINT Server Attivo!</h1></body></html>")

    def log_message(self, format, *args):
        return

def run_dummy_server(port=8080):
    server_address = ('', port)
    httpd = HTTPServer(server_address, DummyHTTPServerHandler)
    print(f"Server HTTP Dummy in ascolto sulla porta {port}...")
    httpd.serve_forever()

# -------------------------------------------------------------
# AVVIO DEL PROGRAMMA
# -------------------------------------------------------------
if __name__ == "__main__":
    # Avvia il server dummy su un thread in background
    server_thread = threading.Thread(target=run_dummy_server, kwargs={'port': 8080}, daemon=True)
    server_thread.start()
    
    # Avvia il bot sul thread principale
    try:
        bot_polling_loop()
    except KeyboardInterrupt:
        print("\nBot arrestato manualmente.")

import json
import time
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
import requests

# -------------------------------------------------------------
# CONFIGURAZIONE
# -------------------------------------------------------------
# Inserisci qui il Token del tuo Bot Telegram preso da @BotFather
BOT_TOKEN = "8221208999:AAE52kQ-ouyyFMPv6D0JqMFChMqdG_UWt2c"
# Inserisci qui l'URL dell'API esterna per le ricerche
EXTERNAL_API_URL = ""

BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

# Dizionario per gestire lo stato della conversazione per ogni utente
# Stati possibili: None (default), 'AWAITING_PHONE', 'AWAITING_USERNAME', 'AWAITING_SOCIAL_ID'
USER_STATES = {}

# -------------------------------------------------------------
# FUNZIONI API DI TELEGRAM
# -------------------------------------------------------------
def send_message(chat_id, text, reply_markup=None):
    """Invia un messaggio a una chat specifica usando l'endpoint sendMessage."""
    url = f"{BASE_URL}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML"
    }
    if reply_markup:
        payload["reply_markup"] = json.dumps(reply_markup)
        
    try:
        response = requests.post(url, json=payload)
        return response.json()
    except Exception as e:
        print(f"Errore nell'invio del messaggio: {e}")
        return None

def handle_updates(updates):
    """Elabora i messaggi in entrata ricevuti da Telegram."""
    for update in updates:
        if "message" not in update or "text" not in update["message"]:
            continue
            
        message = update["message"]
        chat_id = message["chat"]["id"]
        text = message["text"].strip()
        
        # 1. Gestione comando /start
        if text == "/start":
            USER_STATES[chat_id] = None  # Reset dello stato
            welcome_text = "Benvenuto! Scegli un'opzione dalla tastiera in basso per avviare la ricerca OSINT."
            
            # Tastiera personalizzata con i tre pulsanti richiesti
            keyboard = {
                "keyboard": [
                    [{"text": "📱 Phone Lookup"}, {"text": "🔎 username"}],
                    [{"text": "🕵️ id"}]
                ],
                "resize_keyboard": True,
                "one_time_keyboard": False
            }
            send_message(chat_id, welcome_text, reply_markup=keyboard)
            
        # 2. Gestione pressione del pulsante "📱 Phone Lookup"
        elif text == "📱 Phone Lookup":
            USER_STATES[chat_id] = 'AWAITING_PHONE'
            send_message(chat_id, "📞 Scrivi un numero di telefono:")
            
        # 3. Gestione pressione del pulsante "🔎 username"
        elif text == "🔎 username":
            USER_STATES
