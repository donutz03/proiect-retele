# News Channel System - Testing Guide with Console Notifications (TCP, fără autentificare)

kill -9 $(lsof -ti :3333)

## 🧪 Complete Testing Walkthrough

Acest ghid arată **exact** ce output să aștepți la testarea sistemului de notificări, folosind doar TCP și fără autentificare.

## Step 1: Start the Server

**Command:**

```bash
python server.py
```

**Expected Output:**

```
Server running on 127.0.0.1:3333 (TCP)
```

## Step 2: Start Client 1 (Terminal 1)

**Command:**

```bash
python client.py
```

**Expected Output:**

```
Welcome to the News Channel System! (TCP)
Commands:
  list_channels - Show all available channels
  create_channel "<channel name>" "<description>"
  delete_channel "<channel name>"
  subscribe "<channel name>"
  unsubscribe "<channel name>"
  publish_news "<channel name>" <news content>
  my_subscriptions - Show your subscriptions
  exit
✅ Notification system ready!
>
```

## Step 3: Start Client 2 (Terminal 2)

**Command:**

```bash
python client.py
```

**Expected Output:**

```
Welcome to the News Channel System! (TCP)
Commands:
  list_channels - Show all available channels
  create_channel "<channel name>" "<description>"
  delete_channel "<channel name>"
  subscribe "<channel name>"
  unsubscribe "<channel name>"
  publish_news "<channel name>" <news content>
  my_subscriptions - Show your subscriptions
  exit
✅ Notification system ready!
>
```

## Step 4: Test Channel Creation Notification

**Client 1 types:**

```
create_channel "Tech News" "Latest technology updates"
```

**Server Console shows:**

```
📺 Channel creation: 'Tech News' created by 127.0.0.1:XXXXX -> success
```

**Client 2 Console shows:**

```
📨 NOTIFICATION RECEIVED from ('127.0.0.1', 3333): new_channel

🆕 New channel 'Tech News' created
   Tech News - Latest technology updates
   Created by: 127.0.0.1:XXXXX
>
```

## Step 5: Test Subscription

**Client 2 types:**

```
subscribe "Tech News"
```

**Server Console shows:**

```
➕ Subscription: 127.0.0.1:YYYYY to 'Tech News' -> success
```

## Step 6: Test News Publishing with Subscriber Notifications

**Client 1 types:**

```
publish_news "Tech News" Breaking: New AI breakthrough announced by researchers!
```

**Server Console shows:**

```
📰 News publication: 127.0.0.1:XXXXX to 'Tech News' -> success
```

**Client 2 Console shows:**

```
📨 NOTIFICATION RECEIVED from ('127.0.0.1', 3333): new_news

📰 New news in channel 'Tech News':
   [YYYY-MM-DD HH:MM:SS] 127.0.0.1:XXXXX: Breaking: New AI breakthrough announced by researchers!
>
```

## Step 7: Test Content Filtering

**Client 1 types:**

```
publish_news "Tech News" This news contains spam content that should be blocked
```

**Server Console shows:**

```
📰 News publication: 127.0.0.1:XXXXX to 'Tech News' -> error
```

**Client 1 Console shows:**

```
Failed to publish news: News content contains forbidden words and has been blocked
```

**Client 2 Console shows:** _(No notification - correctly filtered)_

## Step 8: Test Channel Deletion

**Client 1 types:**

```
delete_channel "Tech News"
```

**Server Console shows:**

```
🗑️ Channel deletion: 'Tech News' by 127.0.0.1:XXXXX -> success
```

**Client 2 Console shows:**

```
📨 NOTIFICATION RECEIVED from ('127.0.0.1', 3333): channel_deleted

🗑️ Channel 'Tech News' has been deleted
>
```

## 🎯 Key Things to Verify

### ✅ Server Console Should Show:

- Toate notificările trimise (creare/ștergere canal, știri)
- Succesul notificărilor
- Toate cererile primite de la clienți
- Content filtering activ

### ✅ Client Consoles Should Show:

- Confirmări de primire notificări
- Notificări de canal nou/șters (toți clienții)
- Notificări de știri (doar abonații)
- Pornirea sistemului de notificări

### ✅ Verification Points:

1. **Global Notifications**: Crearea/ștergerea canalului notifică TOȚI clienții
2. **Subscriber-Only Notifications**: Știrile merg doar la abonați
3. **Content Filtering**: Cuvintele interzise blochează publicarea
4. **No Notifications**: Clienții neabonați nu primesc știri
5. **Console Logging**: Vizibilitate clară a activității de notificare

## 🚀 Quick Test Commands

**Terminal 1 (Server):**

```bash
python server.py
```

**Terminal 2 (Client 1):**

```
create_channel "Test Channel" "Testing notifications"
publish_news "Test Channel" This is a test message
```

**Terminal 3 (Client 2):**

```
subscribe "Test Channel"
```

Urmărește consola serverului pentru loguri de notificare și consola clientului 2 pentru notificări primite!

## 🔧 Troubleshooting

Dacă notificările nu funcționează:

1. Verifică dacă portul de notificare este afișat la pornirea clientului
2. Asigură-te că serverul primește cereri și trimite notificări
3. Clienții trebuie să afișeze "📨 NOTIFICATION RECEIVED" la primirea notificărilor
4. Repornește clienții dacă thread-ul de notificare nu pornește

Sistemul oferă acum vizibilitate completă pentru notificări, fără autentificare și doar pe TCP! 🎉
