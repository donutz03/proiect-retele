import socket
import json
import threading
import time

HOST = "127.0.0.1"
SERVER_PORT = 3333

class Client:
    def __init__(self):
        self.sock = None
        self.notification_sock = None
        self.notification_port = None
        self.receive_thread = None
        self.channels = []
        self.connection_lock = threading.Lock()

    def connect_to_server(self):
        if self.sock:
            self.sock.close()
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((HOST, SERVER_PORT))

    def setup_notification_listener(self):
        self.notification_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.notification_sock.bind(('', 0))
        self.notification_port = self.notification_sock.getsockname()[1]
        self.notification_sock.listen(5)

    def send_request(self, request):
        with self.connection_lock:
            if not self.sock:
                self.connect_to_server()
            message = json.dumps(request).encode()
            self.sock.sendall(len(message).to_bytes(4, 'big'))
            self.sock.sendall(message)
            length_bytes = self.receive_exact(4)
            if not length_bytes:
                return {"status": "error", "message": "No response from server"}
            resp_len = int.from_bytes(length_bytes, 'big')
            resp_bytes = self.receive_exact(resp_len)
            if not resp_bytes:
                return {"status": "error", "message": "No response from server"}
            return json.loads(resp_bytes.decode())

    def receive_exact(self, n):
        data = b''
        while len(data) < n:
            packet = self.sock.recv(n - len(data))
            if not packet:
                return None
            data += packet
        return data

    def list_channels(self):
        response = self.send_request({"type": "list_channels"})
        if response["status"] == "success":
            self.channels = response["channels"]
            print("\nAvailable channels:")
            self.display_channels()
        else:
            print(f"Failed to get channels: {response['message']}")

    def display_channels(self):
        if not self.channels:
            print("  No channels available")
        else:
            for i, channel in enumerate(self.channels):
                print(f"  {i+1}. {channel['name']} - {channel['description']}")
                print(f"     Creator: {channel['creator']}, Subscribers: {channel['subscriber_count']}")

    def create_channel(self, channel_name, description):
        response = self.send_request({
            "type": "create_channel",
            "channel_name": channel_name,
            "description": description,
            "notification_port": self.notification_port
        })
        print(response["message"])

    def delete_channel(self, channel_name):
        response = self.send_request({"type": "delete_channel", "channel_name": channel_name})
        print(response["message"])

    def subscribe(self, channel_name):
        response = self.send_request({"type": "subscribe", "channel_name": channel_name})
        print(response["message"])

    def unsubscribe(self, channel_name):
        response = self.send_request({"type": "unsubscribe", "channel_name": channel_name})
        print(response["message"])

    def publish_news(self, channel_name, content):
        response = self.send_request({"type": "publish_news", "channel_name": channel_name, "content": content})
        if response["status"] == "success":
            print("News published successfully")
        else:
            print(f"Failed to publish news: {response['message']}")

    def get_subscriptions(self):
        response = self.send_request({"type": "get_subscriptions"})
        if response["status"] == "success":
            subscriptions = response["subscriptions"]
            print("\nYour subscriptions:")
            if not subscriptions:
                print("  No subscriptions")
            else:
                for i, channel in enumerate(subscriptions):
                    print(f"  {i+1}. {channel['name']} - {channel['description']}")
        else:
            print(f"Failed to get subscriptions: {response['message']}")

    def receive_notifications(self):
        print(f"🔔 Notification listener started on port {self.notification_port}")
        while True:
            try:
                client_socket, addr = self.notification_sock.accept()
                threading.Thread(target=self.handle_notification, args=(client_socket, addr), daemon=True).start()
            except Exception as e:
                print(f"\n❌ Error accepting notification connection: {str(e)}")
                continue

    def handle_notification(self, client_socket, addr):
        try:
            length_bytes = self.receive_exact_from_socket(client_socket, 4)
            if not length_bytes:
                return
            notif_len = int.from_bytes(length_bytes, 'big')
            notif_bytes = self.receive_exact_from_socket(client_socket, notif_len)
            if not notif_bytes:
                return
            notification = json.loads(notif_bytes.decode())
            print(f"\n📨 NOTIFICATION RECEIVED from {addr}: {notification.get('type', 'unknown')}")
            if not isinstance(notification, dict) or 'type' not in notification:
                return
            if notification["type"] == "new_channel":
                print(f"\n🆕 {notification['message']}")
                channel = notification["channel"]
                print(f"   {channel['name']} - {channel['description']}")
                print(f"   Created by: {channel['creator']}")
            elif notification["type"] == "channel_deleted":
                print(f"\n🗑️ {notification['message']}")
            elif notification["type"] == "new_news":
                news = notification["news"]
                print(f"\n📰 New news in channel '{notification['channel_name']}':")
                print(f"   [{news['timestamp']}] {news['author']}: {news['content']}")
            print("> ", end="", flush=True)
        except Exception as e:
            print(f"\n❌ Error handling notification: {str(e)}")
        finally:
            client_socket.close()

    def receive_exact_from_socket(self, sock, n):
        data = b''
        while len(data) < n:
            packet = sock.recv(n - len(data))
            if not packet:
                return None
            data += packet
        return data

    def announce_notification_port(self):
        self.send_request({
            "type": "notification_hello",
            "notification_port": self.notification_port
        })

    def start(self):
        print("Welcome to the News Channel System! (TCP)")
        print("Commands:")
        print("  list_channels - Show all available channels")
        print("  create_channel \"<channel name>\" \"<description>\"")
        print("  delete_channel \"<channel name>\"")
        print("  subscribe \"<channel name>\"")
        print("  unsubscribe \"<channel name>\"")
        print("  publish_news \"<channel name>\" <news content>")
        print("  my_subscriptions - Show your subscriptions")
        print("  exit")
        self.setup_notification_listener()
        self.announce_notification_port()
        self.receive_thread = threading.Thread(target=self.receive_notifications, daemon=True)
        self.receive_thread.start()
        print("✅ Notification system ready!")
        while True:
            try:
                command = input("> ").strip()
                if command == "exit":
                    break
                parts = []
                current = ""
                in_quotes = False
                for char in command:
                    if char == '"':
                        in_quotes = not in_quotes
                    elif char == ' ' and not in_quotes:
                        if current:
                            parts.append(current)
                            current = ""
                    else:
                        current += char
                if current:
                    parts.append(current)
                if not parts:
                    continue
                cmd = parts[0]
                args = parts[1:]
                if cmd == "list_channels" and len(args) == 0:
                    self.list_channels()
                elif cmd == "create_channel" and len(args) == 2:
                    self.create_channel(args[0], args[1])
                elif cmd == "delete_channel" and len(args) == 1:
                    self.delete_channel(args[0])
                elif cmd == "subscribe" and len(args) == 1:
                    self.subscribe(args[0])
                elif cmd == "unsubscribe" and len(args) == 1:
                    self.unsubscribe(args[0])
                elif cmd == "publish_news" and len(args) >= 2:
                    channel_name = args[0]
                    content = " ".join(args[1:])
                    self.publish_news(channel_name, content)
                elif cmd == "my_subscriptions" and len(args) == 0:
                    self.get_subscriptions()
                else:
                    print("Invalid command or arguments")
                    print("Use 'exit' to quit")
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Error: {e}")
        if self.sock:
            self.sock.close()
        if self.notification_sock:
            self.notification_sock.close()

if __name__ == "__main__":
    client = Client()
    client.start() 