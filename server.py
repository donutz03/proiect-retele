import socket
import json
import threading
from datetime import datetime

HOST = "127.0.0.1"
PORT = 3333

class Message:
    def __init__(self, content, author, timestamp):
        self.content = content
        self.author = author
        self.timestamp = timestamp

    def to_dict(self):
        return {
            "content": self.content,
            "author": self.author,
            "timestamp": self.timestamp
        }

class Channel:
    def __init__(self, name, description, creator):
        self.name = name
        self.description = description
        self.creator = creator
        self.news = []
        self.subscribers = set()  # Set of usernames

    def add_news(self, content, author):
        news = Message(content, author, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        self.news.append(news)
        return news

    def subscribe(self, username):
        self.subscribers.add(username)

    def unsubscribe(self, username):
        self.subscribers.discard(username)

    def to_dict(self):
        return {
            "name": self.name,
            "description": self.description,
            "creator": self.creator,
            "subscriber_count": len(self.subscribers)
        }

class Server:
    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((HOST, PORT))
        self.users = {}  # username -> password
        self.channels = {}  # channel_name -> Channel object
        self.client_addresses = {}  # username -> (ip, port)
        self.client_notification_ports = {}  # username -> notification_port
        self.lock = threading.Lock()
        
        # Predefined forbidden words for content filtering
        self.forbidden_words = ["spam", "hack", "virus", "malware", "phishing", "scam"]

    def content_filter(self, content):
        """Filter content to check for forbidden words"""
        content_lower = content.lower()
        for word in self.forbidden_words:
            if word in content_lower:
                return False
        return True

    def handle_register(self, username, password, client_addr, notification_port):
        with self.lock:
            if username in self.users:
                return {"status": "error", "message": "Username already exists"}
            self.users[username] = password
            self.client_addresses[username] = client_addr
            self.client_notification_ports[username] = notification_port
            return {"status": "success", "message": "Registration successful"}

    def handle_login(self, username, password, client_addr, notification_port):
        with self.lock:
            if username in self.users and self.users[username] == password:
                self.client_addresses[username] = client_addr
                self.client_notification_ports[username] = notification_port
                # Send current channels list
                channels_list = [channel.to_dict() for channel in self.channels.values()]
                return {
                    "status": "success", 
                    "message": "Login successful", 
                    "channels": channels_list
                }
            return {"status": "error", "message": "Invalid credentials"}

    def handle_list_channels(self, username):
        with self.lock:
            channels_list = [channel.to_dict() for channel in self.channels.values()]
            return {"status": "success", "channels": channels_list}

    def handle_create_channel(self, channel_name, description, username):
        with self.lock:
            if channel_name in self.channels:
                return {"status": "error", "message": "Channel already exists"}
            
            channel = Channel(channel_name, description, username)
            self.channels[channel_name] = channel
            
            # Notify all clients about the new channel
            def notify_async():
                try:
                    self.notify_all_clients({
                        "type": "new_channel",
                        "channel": channel.to_dict(),
                        "message": f"New channel '{channel_name}' created by {username}"
                    })
                except Exception as e:
                    pass
            
            threading.Thread(target=notify_async).start()
            
            return {"status": "success", "message": f"Channel '{channel_name}' created"}

    def handle_delete_channel(self, channel_name, username):
        with self.lock:
            if channel_name not in self.channels:
                return {"status": "error", "message": "Channel does not exist"}
            
            channel = self.channels[channel_name]
            if channel.creator != username:
                return {"status": "error", "message": "Only the channel creator can delete it"}
            
            del self.channels[channel_name]
            
            # Notify all clients about the deleted channel
            def notify_async():
                try:
                    self.notify_all_clients({
                        "type": "channel_deleted",
                        "channel_name": channel_name,
                        "message": f"Channel '{channel_name}' has been deleted by {username}"
                    })
                except Exception as e:
                    pass
            
            threading.Thread(target=notify_async).start()
            
            return {"status": "success", "message": f"Channel '{channel_name}' deleted"}

    def handle_subscribe(self, channel_name, username):
        with self.lock:
            if channel_name not in self.channels:
                return {"status": "error", "message": "Channel does not exist"}
            
            channel = self.channels[channel_name]
            channel.subscribe(username)
            
            return {"status": "success", "message": f"Subscribed to channel '{channel_name}'"}

    def handle_unsubscribe(self, channel_name, username):
        with self.lock:
            if channel_name not in self.channels:
                return {"status": "error", "message": "Channel does not exist"}
            
            channel = self.channels[channel_name]
            channel.unsubscribe(username)
            
            return {"status": "success", "message": f"Unsubscribed from channel '{channel_name}'"}

    def handle_publish_news(self, channel_name, content, username):
        with self.lock:
            if channel_name not in self.channels:
                return {"status": "error", "message": "Channel does not exist"}
            
            channel = self.channels[channel_name]
            if channel.creator != username:
                return {"status": "error", "message": "Only the channel creator can publish news"}
            
            # Filter content for forbidden words
            if not self.content_filter(content):
                return {
                    "status": "error", 
                    "message": "News content contains forbidden words and has been blocked"
                }
            
            news = channel.add_news(content, username)
            
            # Notify only subscribers
            def notify_async():
                try:
                    self.notify_subscribers(channel, {
                        "type": "new_news",
                        "channel_name": channel_name,
                        "news": news.to_dict(),
                        "message": f"New news in channel '{channel_name}'"
                    })
                except Exception as e:
                    pass
            
            threading.Thread(target=notify_async).start()
            
            return {"status": "success", "message": "News published successfully"}

    def handle_get_subscriptions(self, username):
        with self.lock:
            subscriptions = []
            for channel in self.channels.values():
                if username in channel.subscribers:
                    subscriptions.append(channel.to_dict())
            return {"status": "success", "subscriptions": subscriptions}

    def notify_all_clients(self, notification):
        with self.lock:
            print(f"📢 SENDING NOTIFICATION TO ALL CLIENTS: {notification['type']}")
            clients_notified = 0
            for username in self.client_notification_ports:
                try:
                    notification_port = self.client_notification_ports[username]
                    client_addr = self.client_addresses[username]
                    notification_addr = (client_addr[0], notification_port)
                    message = json.dumps(notification)
                    self.sock.sendto(message.encode(), notification_addr)
                    print(f"   ✅ Notified {username} at {notification_addr}")
                    clients_notified += 1
                except Exception as e:
                    print(f"   ❌ Failed to notify {username}: {e}")
            print(f"📊 Total clients notified: {clients_notified}")
            print("="*50)

    def notify_subscribers(self, channel, notification):
        with self.lock:
            print(f"📰 SENDING NEWS TO SUBSCRIBERS of '{channel.name}': {notification['type']}")
            subscribers_notified = 0
            for username in channel.subscribers:
                try:
                    if username in self.client_notification_ports:
                        notification_port = self.client_notification_ports[username]
                        client_addr = self.client_addresses[username]
                        notification_addr = (client_addr[0], notification_port)
                        message = json.dumps(notification)
                        self.sock.sendto(message.encode(), notification_addr)
                        print(f"   ✅ Notified subscriber {username} at {notification_addr}")
                        subscribers_notified += 1
                    else:
                        print(f"   ⚠️ Subscriber {username} not connected")
                except Exception as e:
                    print(f"   ❌ Failed to notify subscriber {username}: {e}")
            print(f"📊 Total subscribers notified: {subscribers_notified}/{len(channel.subscribers)}")
            print("="*50)

    def run(self):
        print(f"Server running on {HOST}:{PORT}")
        print("News Channel Server - Content filtering enabled")
        print(f"Forbidden words: {', '.join(self.forbidden_words)}")
        
        while True:
            try:
                data, addr = self.sock.recvfrom(4096)
                try:
                    request = json.loads(data.decode())
                    
                    if not isinstance(request, dict) or 'type' not in request:
                        response = {"status": "error", "message": "Invalid request format"}
                        self.sock.sendto(json.dumps(response).encode(), addr)
                        continue

                    print(f"🔄 Received request: {request['type']} from {addr}")
                    
                    response = None
                    if request["type"] == "register":
                        response = self.handle_register(
                            request["username"],
                            request["password"],
                            addr,
                            request.get("notification_port", 0)
                        )
                        print(f"📝 Registration attempt: {request['username']} -> {response['status']}")
                    elif request["type"] == "login":
                        response = self.handle_login(
                            request["username"],
                            request["password"],
                            addr,
                            request.get("notification_port", 0)
                        )
                        print(f"🔐 Login attempt: {request['username']} -> {response['status']}")
                    elif request["type"] == "list_channels":
                        if "username" not in request:
                            response = {"status": "error", "message": "Username not provided"}
                        else:
                            response = self.handle_list_channels(request["username"])
                    elif request["type"] == "create_channel":
                        if "username" not in request:
                            response = {"status": "error", "message": "Username not provided"}
                        else:
                            response = self.handle_create_channel(
                                request["channel_name"],
                                request["description"],
                                request["username"]
                            )
                            print(f"📺 Channel creation: '{request['channel_name']}' by {request['username']} -> {response['status']}")
                    elif request["type"] == "delete_channel":
                        if "username" not in request:
                            response = {"status": "error", "message": "Username not provided"}
                        else:
                            response = self.handle_delete_channel(
                                request["channel_name"],
                                request["username"]
                            )
                            print(f"🗑️ Channel deletion: '{request['channel_name']}' by {request['username']} -> {response['status']}")
                    elif request["type"] == "subscribe":
                        if "username" not in request:
                            response = {"status": "error", "message": "Username not provided"}
                        else:
                            response = self.handle_subscribe(
                                request["channel_name"],
                                request["username"]
                            )
                            print(f"➕ Subscription: {request['username']} to '{request['channel_name']}' -> {response['status']}")
                    elif request["type"] == "unsubscribe":
                        if "username" not in request:
                            response = {"status": "error", "message": "Username not provided"}
                        else:
                            response = self.handle_unsubscribe(
                                request["channel_name"],
                                request["username"]
                            )
                            print(f"➖ Unsubscription: {request['username']} from '{request['channel_name']}' -> {response['status']}")
                    elif request["type"] == "publish_news":
                        if "username" not in request:
                            response = {"status": "error", "message": "Username not provided"}
                        else:
                            response = self.handle_publish_news(
                                request["channel_name"],
                                request["content"],
                                request["username"]
                            )
                            print(f"📰 News publication: {request['username']} to '{request['channel_name']}' -> {response['status']}")
                            if response['status'] == 'error' and 'forbidden words' in response['message']:
                                print(f"🚫 Content filtered: '{request['content'][:50]}...')")
                    elif request["type"] == "get_subscriptions":
                        if "username" not in request:
                            response = {"status": "error", "message": "Username not provided"}
                        else:
                            response = self.handle_get_subscriptions(request["username"])

                    if response:
                        self.sock.sendto(json.dumps(response).encode(), addr)
                    else:
                        response = {"status": "error", "message": "Unknown request type"}
                        self.sock.sendto(json.dumps(response).encode(), addr)

                except json.JSONDecodeError:
                    response = {"status": "error", "message": "Invalid JSON format"}
                    self.sock.sendto(json.dumps(response).encode(), addr)
                except Exception as e:
                    response = {"status": "error", "message": "Internal server error"}
                    self.sock.sendto(json.dumps(response).encode(), addr)

            except Exception as e:
                pass

if __name__ == "__main__":
    server = Server()
    server.run()