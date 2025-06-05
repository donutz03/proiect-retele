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
        self.subscribers = set()  # Set of client_ids

    def add_news(self, content, author):
        news = Message(content, author, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        self.news.append(news)
        return news

    def subscribe(self, client_id):
        self.subscribers.add(client_id)

    def unsubscribe(self, client_id):
        self.subscribers.discard(client_id)

    def to_dict(self):
        return {
            "name": self.name,
            "description": self.description,
            "creator": self.creator,
            "subscriber_count": len(self.subscribers)
        }

class Server:
    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((HOST, PORT))
        self.channels = {}  # channel_name -> Channel object
        self.client_notification_ports = {}  # client_id -> notification_port
        self.client_addresses = {}  # client_id -> (ip, port)
        self.lock = threading.Lock()
        self.forbidden_words = ["spam", "hack", "virus", "malware", "phishing", "scam"]

    def content_filter(self, content):
        """Filter content to check for forbidden words"""
        content_lower = content.lower()
        for word in self.forbidden_words:
            if word in content_lower:
                return False
        return True

    def handle_list_channels(self):
        with self.lock:
            channels_list = [channel.to_dict() for channel in self.channels.values()]
            return {"status": "success", "channels": channels_list}

    def handle_create_channel(self, channel_name, description, client_id):
        with self.lock:
            if channel_name in self.channels:
                return {"status": "error", "message": "Channel already exists"}
            channel = Channel(channel_name, description, client_id)
            self.channels[channel_name] = channel
            def notify_async():
                try:
                    self.notify_all_clients({
                        "type": "new_channel",
                        "channel": channel.to_dict(),
                        "message": f"New channel '{channel_name}' created"
                    })
                except Exception:
                    pass
            threading.Thread(target=notify_async, daemon=True).start()
            return {"status": "success", "message": f"Channel '{channel_name}' created"}

    def handle_delete_channel(self, channel_name, client_id):
        with self.lock:
            if channel_name not in self.channels:
                return {"status": "error", "message": "Channel does not exist"}
            channel = self.channels[channel_name]
            if channel.creator != client_id:
                return {"status": "error", "message": "Only the channel creator can delete it"}
            del self.channels[channel_name]
            def notify_async():
                try:
                    self.notify_all_clients({
                        "type": "channel_deleted",
                        "channel_name": channel_name,
                        "message": f"Channel '{channel_name}' has been deleted"
                    })
                except Exception:
                    pass
            threading.Thread(target=notify_async, daemon=True).start()
            return {"status": "success", "message": f"Channel '{channel_name}' deleted"}

    def handle_subscribe(self, channel_name, client_id):
        with self.lock:
            if channel_name not in self.channels:
                return {"status": "error", "message": "Channel does not exist"}
            channel = self.channels[channel_name]
            channel.subscribe(client_id)
            return {"status": "success", "message": f"Subscribed to channel '{channel_name}'"}

    def handle_unsubscribe(self, channel_name, client_id):
        with self.lock:
            if channel_name not in self.channels:
                return {"status": "error", "message": "Channel does not exist"}
            channel = self.channels[channel_name]
            channel.unsubscribe(client_id)
            return {"status": "success", "message": f"Unsubscribed from channel '{channel_name}'"}

    def handle_publish_news(self, channel_name, content, client_id):
        with self.lock:
            if channel_name not in self.channels:
                return {"status": "error", "message": "Channel does not exist"}
            channel = self.channels[channel_name]
            if channel.creator != client_id:
                return {"status": "error", "message": "Only the channel creator can publish news"}
            if not self.content_filter(content):
                return {"status": "error", "message": "News content contains forbidden words and has been blocked"}
            news = channel.add_news(content, client_id)
            def notify_async():
                try:
                    self.notify_subscribers(channel, {
                        "type": "new_news",
                        "channel_name": channel_name,
                        "news": news.to_dict(),
                        "message": f"New news in channel '{channel_name}'"
                    })
                except Exception:
                    pass
            threading.Thread(target=notify_async, daemon=True).start()
            return {"status": "success", "message": "News published successfully"}

    def handle_get_subscriptions(self, client_id):
        with self.lock:
            subscriptions = []
            for channel in self.channels.values():
                if client_id in channel.subscribers:
                    subscriptions.append(channel.to_dict())
            return {"status": "success", "subscriptions": subscriptions}

    def notify_all_clients(self, notification):
        with self.lock:
            for client_id in self.client_notification_ports:
                try:
                    host, port = self.client_addresses[client_id]
                    self.send_notification(host, port, notification)
                except Exception:
                    pass

    def notify_subscribers(self, channel, notification):
        with self.lock:
            for client_id in channel.subscribers:
                try:
                    if client_id in self.client_notification_ports:
                        host, port = self.client_addresses[client_id]
                        self.send_notification(host, port, notification)
                except Exception:
                    pass

    def send_notification(self, host, port, notification):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((host, port))
            message = json.dumps(notification).encode()
            sock.sendall(len(message).to_bytes(4, 'big'))
            sock.sendall(message)
            sock.close()
        except Exception:
            pass

    def receive_exact(self, sock, n):
        data = b''
        while len(data) < n:
            packet = sock.recv(n - len(data))
            if not packet:
                return None
            data += packet
        return data

    def handle_notification_hello(self, client_id, notification_port, client_addr):
        with self.lock:
            self.client_notification_ports[client_id] = notification_port
            self.client_addresses[client_id] = (client_addr[0], notification_port)

    def handle_client(self, client_socket, client_addr):
        client_id = f"{client_addr[0]}:{client_addr[1]}"
        try:
            while True:
                length_bytes = self.receive_exact(client_socket, 4)
                if not length_bytes:
                    break
                msg_len = int.from_bytes(length_bytes, 'big')
                data = self.receive_exact(client_socket, msg_len)
                if not data:
                    break
                try:
                    request = json.loads(data.decode())
                    req_type = request.get("type")
                    if req_type == "notification_hello":
                        self.handle_notification_hello(client_id, request.get("notification_port", 0), client_addr)
                        response = {"status": "success", "message": "Notification port registered"}
                    elif req_type == "list_channels":
                        response = self.handle_list_channels()
                    elif req_type == "create_channel":
                        response = self.handle_create_channel(request["channel_name"], request["description"], client_id)
                        if response["status"] == "success":
                            self.client_notification_ports[client_id] = request.get("notification_port", 0)
                            self.client_addresses[client_id] = (client_addr[0], request.get("notification_port", 0))
                    elif req_type == "delete_channel":
                        response = self.handle_delete_channel(request["channel_name"], client_id)
                    elif req_type == "subscribe":
                        response = self.handle_subscribe(request["channel_name"], client_id)
                    elif req_type == "unsubscribe":
                        response = self.handle_unsubscribe(request["channel_name"], client_id)
                    elif req_type == "publish_news":
                        response = self.handle_publish_news(request["channel_name"], request["content"], client_id)
                    elif req_type == "get_subscriptions":
                        response = self.handle_get_subscriptions(client_id)
                    else:
                        response = {"status": "error", "message": "Unknown request type"}
                    resp_bytes = json.dumps(response).encode()
                    client_socket.sendall(len(resp_bytes).to_bytes(4, 'big'))
                    client_socket.sendall(resp_bytes)
                except Exception:
                    error = {"status": "error", "message": "Invalid request format"}
                    err_bytes = json.dumps(error).encode()
                    client_socket.sendall(len(err_bytes).to_bytes(4, 'big'))
                    client_socket.sendall(err_bytes)
        finally:
            client_socket.close()

    def run(self):
        self.sock.listen(5)
        print(f"Server running on {HOST}:{PORT} (TCP)")
        while True:
            client_socket, client_addr = self.sock.accept()
            threading.Thread(target=self.handle_client, args=(client_socket, client_addr), daemon=True).start()

if __name__ == "__main__":
    server = Server()
    server.run()