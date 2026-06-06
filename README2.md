# 🖥️ PC Remote Controller

Controlla il tuo PC dal telefono via rete locale (WiFi o LAN).
Non serve internet — funziona su rete locale.
Ogni sessione ha un codice univoco per sicurezza.

---

## 📦 INSTALLAZIONE (una sola volta)

### 1. Installa dipendenze Python
```bash
pip install psutil
```

### 2. Metti i due file nella stessa cartella:
- `pc_controller_server.py`
- `pc_controller_mobile.html`

---

## 🚀 AVVIO

### Sul PC:
```bash
python pc_controller_server.py
```

Vedrai qualcosa come:
```
╔══════════════════════════════════════════════════════╗
║         PC REMOTE CONTROLLER - SERVER                ║
╠══════════════════════════════════════════════════════╣
║  IP Server  : 192.168.1.15                           ║
║  Porta      : 8765                                   ║
║  Codice     : A3X7KQ                                 ║
╠══════════════════════════════════════════════════════╣
║  Mobile URL : http://192.168.1.15:8765/              ║
╚══════════════════════════════════════════════════════╝
```

### Sul telefono:
1. Connettiti alla **stessa rete WiFi** del PC
2. Apri il browser e vai su: `http://[IP]:8765`
   - Oppure apri il file `pc_controller_mobile.html` direttamente
3. Inserisci **IP** e **Codice** mostrati nel terminale
4. Clicca **Connetti**

---

## 🔑 SISTEMA CODICI

- Ad ogni avvio del server viene generato **un codice nuovo**
- Il codice è valido per **24 ore**
- Puoi generare nuovi codici dalla tab **⚡ Sistema** > **Genera Nuovo Codice**
- **Più dispositivi** possono usare lo stesso codice contemporaneamente
- Solo chi ha il codice può controllare il PC

---

## ✨ FUNZIONALITÀ

| Funzione | Descrizione |
|----------|-------------|
| 📊 Dashboard | CPU, RAM, Disco, info sistema |
| ⚙️ Processi | Vedi e chiudi app in esecuzione |
| ▶️ Apri App | Lancia applicazioni per nome |
| 📁 File | Sfoglia, crea, elimina file |
| 🔍 Cerca File | Ricerca file per nome |
| 🌐 Web | Cerca su Google, apri siti |
| ✏️ Testo | Scrivi testo, si apre in editor sul PC |
| 💻 Shell | Esegui comandi cmd/bash |
| 🔧 Impostazioni | Apre le impostazioni di sistema |
| 🔴 Spegni | Spegne il PC (con countdown) |
| 🔁 Riavvia | Riavvia il PC (con countdown) |

---

## ⚠️ NOTE DI SICUREZZA

- Usa **solo su reti di fiducia** (casa tua, ufficio)
- Non esporre la porta 8765 su internet
- Il codice protegge da accessi non autorizzati sulla stessa rete
- Lo shell remoto esegue comandi con i tuoi permessi utente

---

## 🛠️ TROUBLESHOOTING

**"Server non raggiungibile"**
- Controlla che PC e telefono siano sulla stessa rete WiFi
- Controlla che il firewall Windows/Mac non blocchi la porta 8765
- Windows: Pannello di Controllo > Firewall > Consenti app > aggiungi Python

**"Codice non valido"**
- Riavvia il server per generare un nuovo codice
- Oppure usa il pulsante "Genera Nuovo Codice" se sei già connesso

**Su Windows: errore firewall**
```
netsh advfirewall firewall add rule name="PC Remote" dir=in action=allow protocol=TCP localport=8765
```
