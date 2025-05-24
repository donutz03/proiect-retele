import socket
import json
import threading
import sys
import time

HOST = "127.0.0.1"
SERVER_PORT = 3333

class Client:
    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.notification_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Bind to port 0 to get a random available port
        self.notification_sock.bind(('', 0))
        self.notification_port = self.notification_sock.getsockname()[1]
        
        self.username = None
        self.is_authenticated = False
        self.receive_thread = None
        self.last_request_time = 0
        self.request_timeout = 5  # seconds
        self.channels = []  # List of available channels

    def send_request(self, request):
        self.last_request_time = time.time()
        self.sock.sendto(json.dumps(request).encode(), (HOST, SERVER_PORT))
        
        # Wait for response with timeout
        while time.time() - self.last_request_time < self.request_timeout:
            try:
                self.sock.settimeout(0.1)  # Small timeout for checking
                data, _ = self.sock.recvfrom(4096)
                try:
                    response = json.loads(data.decode())
                    if isinstance(response, dict) and 'status' in response:
                        return response
                except json.JSONDecodeError:
                    continue
            except socket.timeout:
                continue
            except Exception as e:
                return {"status": "error", "message": f"Failed to receive response: {str(e)}"}
        
        return {"status": "error", "message": "Request timeout"}

    def register(self, username, password):
        response = self.send_request({
            "type": "register",
            "username": username,
            "password": password,
            "notification_port": self.notification_port
        })
        if response["status"] == "success":
            self.username = username
            self.is_authenticated = True
            print("Registration successful!")
        else:
            print(f"Registration failed: {response['message']}")

    def login(self, username, password):
        response = self.send_request({
            "type": "login",
            "username": username,
            "password": password,
            "notification_port": self.notification_port
        })
        if response["status"] == "success":
            self.username = username
            self.is_authenticated = True
            self.channels = response.get("channels", [])
            print("Login successful!")
            print("\nAvailable channels:")
            self.display_channels()
        else:
            print(f"Login failed: {response['message']}")

    def list_channels(self):
        if not self.is_authenticated:
            print("Please login first")
            return
        response = self.send_request({
            "type": "list_channels",
            "username": self.username
        })
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
        if not self.is_authenticated:
            print("Please login first")
            return
        response = self.send_request({
            "type": "create_channel",
            "channel_name": channel_name,
            "description": description,
            "username": self.username
        })
        print(response["message"])

    def delete_channel(self, channel_name):
        if not self.is_authenticated:
            print("Please login first")
            return
        response = self.send_request({
            "type": "delete_channel",
            "channel_name": channel_name,
            "username": self.username
        })
        print(response["message"])

    def subscribe(self, channel_name):
        if not self.is_authenticated:
            print("Please login first")
            return
        response = self.send_request({
            "type": "subscribe",
            "channel_name": channel_name,
            "username": self.username
        })
        print(response["message"])

    def unsubscribe(self, channel_name):
        if not self.is_authenticated:
            print("Please login first")
            return
        response = self.send_request({
            "type": "unsubscribe",
            "channel_name": channel_name,
            "username": self.username
        })
        print(response["message"])

    def publish_news(self, channel_name, content):
        if not self.is_authenticated:
            print("Please login first")
            return
        response = self.send_request({
            "type": "publish_news",
            "channel_name": channel_name,
            "content": content,
            "username": self.username
        })
        if response["status"] == "success":
            print("News published successfully")
        else:
            print(f"Failed to publish news: {response['message']}")

    def get_subscriptions(self):
        if not self.is_authenticated:
            print("Please login first")
            return
        response = self.send_request({
            "type": "get_subscriptions",
            "username": self.username
        })
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
                data, addr = self.notification_sock.recvfrom(4096)
                try:
                    notification = json.loads(data.decode())
                    print(f"\n📨 NOTIFICATION RECEIVED from {addr}: {notification.get('type', 'unknown')}")
                    
                    if not isinstance(notification, dict) or 'type' not in notification:
                        continue
                    
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
                except json.JSONDecodeError:
                    print(f"\n❌ Failed to decode notification: {data}")
                    continue
            except Exception as e:
                print(f"\n❌ Error receiving notification: {str(e)}")
                continue

    def start(self):
        print("Welcome to the News Channel System!")
        print("Commands:")
        print("  register <username> <password>")
        print("  login <username> <password>")
        print("  list_channels - Show all available channels")
        print("  create_channel \"<channel name>\" \"<description>\"")
        print("  delete_channel \"<channel name>\"")
        print("  subscribe \"<channel name>\"")
        print("  unsubscribe \"<channel name>\"")
        print("  publish_news \"<channel name>\" <news content>")
        print("  my_subscriptions - Show your subscriptions")
        print("  exit")
        print(f"\n🔔 Starting notification system on port {self.notification_port}...")

        self.receive_thread = threading.Thread(target=self.receive_notifications)
        self.receive_thread.daemon = True
        self.receive_thread.start()
        print("✅ Notification system ready!")

        while True:
            try:
                command = input("> ").strip()
                if command == "exit":
                    break

                # Parse command with quoted strings
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

                if cmd == "register" and len(args) == 2:
                    self.register(args[0], args[1])
                elif cmd == "login" and len(args) == 2:
                    self.login(args[0], args[1])
                elif cmd == "list_channels" and len(args) == 0:
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

if __name__ == "__main__":
    client = Client()
    client.start() 