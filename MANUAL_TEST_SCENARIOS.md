# Manual Test Scenarios for News Channel System

## 1. Basic Manual Test Scenario

### 1. Pornește serverul

```bash
python3 server.py
```

### 2. Pornește doi clienți (în două terminale diferite)

```bash
python3 client.py
```

### 3. Vezi lista canalelor (ambele clienți)

```
list_channels
```

**Output:**

```
Available channels:
  No channels available
```

### 4. Clientul 1 creează un canal

```
create_channel "Tech" "Tehnologie și inovație"
```

**Client 1:**

```
Channel 'Tech' created
```

**Client 2:**

```
📨 NOTIFICATION RECEIVED ...: new_channel

🆕 New channel 'Tech' created
   Tech - Tehnologie și inovație
   Created by: ...
>
```

### 5. Clientul 2 se abonează la canal

```
subscribe "Tech"
```

**Client 2:**

```
Subscribed to channel 'Tech'
```

### 6. Clientul 1 publică o știre pe canal

```
publish_news "Tech" "Breaking: S-a lansat un nou AI!"
```

**Client 1:**

```
News published successfully
```

**Client 2:**

```
📨 NOTIFICATION RECEIVED ...: new_news

📰 New news in channel 'Tech':
   [data ora] ...: Breaking: S-a lansat un nou AI!
>
```

### 7. Clientul 2 se dezabonează de la canal

```
unsubscribe "Tech"
```

**Client 2:**

```
Unsubscribed from channel 'Tech'
```

### 8. Clientul 1 publică altă știre pe canal

```
publish_news "Tech" "Altă știre importantă!"
```

**Client 1:**

```
News published successfully
```

**Client 2:**
_(Nu trebuie să primească nicio notificare!)_

### 9. Clientul 1 publică o știre cu cuvânt interzis

```
publish_news "Tech" "Aceasta este spam și nu ar trebui să apară"
```

**Client 1:**

```
Failed to publish news: News content contains forbidden words and has been blocked
```

**Client 2:**
_(Nu trebuie să primească nicio notificare!)_

### 10. Clientul 1 șterge canalul

```
delete_channel "Tech"
```

**Client 1:**

```
Channel 'Tech' deleted
```

**Client 2:**

```
📨 NOTIFICATION RECEIVED ...: channel_deleted

🗑️ Channel 'Tech' has been deleted
>
```

### 11. (Opțional) Verifică lista canalelor din nou

```
list_channels
```

**Output:**

```
Available channels:
  No channels available
```

---

## 2. Scenarii suplimentare de testare manuală

### 1. Mai mulți clienți abonați la același canal

- Pornește 3 clienți.
- Clientul 1 creează canalul "Sport".
- Clientul 2 și Clientul 3 se abonează la "Sport".
- Clientul 1 publică o știre pe "Sport".
- **Așteptat:** Ambii clienți abonați (2 și 3) primesc notificarea cu știrea.

### 2. Un client creează două canale diferite

- Clientul 1 creează "Tech" și "Travel".
- Clientul 2 se abonează doar la "Tech".
- Clientul 1 publică știri pe ambele canale.
- **Așteptat:** Clientul 2 primește notificare doar pentru știrea de pe "Tech".

### 3. Un client se abonează, apoi se dezabonează și se reabonează

- Clientul 2 se abonează la "Tech".
- Clientul 2 se dezabonează de la "Tech".
- Clientul 1 publică o știre (Clientul 2 NU trebuie să primească).
- Clientul 2 se reabonează la "Tech".
- Clientul 1 publică altă știre (Clientul 2 TREBUIE să primească).

### 4. Ștergerea unui canal cu abonați

- Clientul 1 creează "News".
- Clientul 2 și 3 se abonează la "News".
- Clientul 1 șterge canalul.
- **Așteptat:** Toți abonații primesc notificare de ștergere.

### 5. Publicare știre pe un canal inexistent

- Clientul 1 încearcă să publice știre pe "Nonexistent".
- **Așteptat:** Primește mesaj de eroare, niciun client nu primește notificare.

### 6. Subscriere la un canal inexistent

- Clientul 2 încearcă să se aboneze la "GhostChannel".
- **Așteptat:** Primește mesaj de eroare.

### 7. Un client încearcă să șteargă un canal creat de altcineva

- Clientul 1 creează "Music".
- Clientul 2 încearcă să șteargă "Music".
- **Așteptat:** Primește mesaj de eroare, canalul nu este șters.

### 8. Publicare știre cu cuvânt interzis (filtrare conținut)

- Clientul 1 publică pe "Tech" o știre cu "spam" sau "virus".
- **Așteptat:** Primește mesaj de eroare, niciun abonat nu primește notificare.

### 9. Listarea canalelor după ștergere

- Creezi și ștergi un canal.
- Faci `list_channels` pe toți clienții.
- **Așteptat:** Canalul nu mai apare la niciun client.

### 10. Subscriere multiplă la același canal

- Clientul 2 dă de două ori `subscribe "Tech"`.
- **Așteptat:** Nu apar erori, dar primește notificare o singură dată la publicare știre.

### 11. Un client nou conectat după ce s-au creat canale

- Clientul 1 creează "News".
- Clientul 2 se conectează după și dă `list_channels`.
- **Așteptat:** Clientul 2 vede canalul "News" în listă.
