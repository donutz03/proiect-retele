import socket
import json
import threading
import sys
import time

HOST = "127.0.0.1"
SERVER_PORT = 3333

class Client:
    def __init__(self):
        self.sock = None
        self.notification_sock = None
        self.notification_port = None
        
        self.username = None
        self.is_authenticated = False
        self.receive_thread = None
        self.channels = []  # List of available channels
        self.connection_lock = threading.Lock()

    def connect_to_server(self):
        """Establish TCP connection to server"""
        try:
            if self.sock:
                self.sock.close()
            
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((HOST, SERVER_PORT))
            return True
        except Exception as e:
            print(f"Failed to connect to server: {e}")
            return False

    def setup_notification_listener(self):
        """Set up TCP notification listener"""
        try:
            self.notification_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.notification_sock.bind(('', 0))  # Bind to any available port
            self.notification_port = self.notification_sock.getsockname()[1]
            self.notification_sock.listen(5)
            return True
        except Exception as e:
            print(f"Failed to setup notification listener: {e}")
            return False

    def send_request(self, request):
        """Send request to server and wait for response"""
        with self.connection_lock:
            try:
                if not self.sock:
                    if not self.connect_to_server():
                        return {"status": "error", "message": "Failed to connect to server"}
                
                # Send request
                message = json.dumps(request)
                message_bytes = message.encode('utf-8')
                message_length = len(message_bytes)
                
                # Send message length first, then the message
                self.sock.sendall(message_length.to_bytes(4, byteorder='big'))
                self.sock.sendall(message_bytes)
                
                # Receive response length
                length_bytes = self.receive_exact(4)
                if not length_bytes:
                    return {"status": "error", "message": "Failed to receive response length"}
                
                response_length = int.from_bytes(length_bytes, byteorder='big')
                
                # Receive response
                response_bytes = self.receive_exact(response_length)
                if not response_bytes:
                    return {"status": "error", "message": "Failed to receive response"}
                
                response = json.loads(response_bytes.decode('utf-8'))
                return response
                
            except Exception as e:
                return {"status": "error", "message": f"Communication error: {str(e)}"}

    def receive_exact(self, n):
        """Receive exactly n bytes from socket"""
        data = b''
        while len(data) < n:
            try:
                packet = self.sock.recv(n - len(data))
                if not packet:
                    return None
                data += packet
            except Exception:
                return None
        return data

    def register(self, username, password):
        if not self.setup_notification_listener():
            print("Failed to setup notification system")
            return
            
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
        if not self.setup_notification_listener():
            print("Failed to setup notification system")
            return
            
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
        """Accept and handle notification connections"""
        print(f"🔔 Notification listener started on port {self.notification_port}")
        while True:
            try:
                client_socket, addr = self.notification_sock.accept()
                # Handle notification in a separate thread
                threading.Thread(target=self.handle_notification, args=(client_socket, addr), daemon=True).start()
            except Exception as e:
                print(f"\n❌ Error accepting notification connection: {str(e)}")
                continue

    def handle_notification(self, client_socket, addr):
        """Handle individual notification connection"""
        try:
            # Receive notification length
            length_bytes = self.receive_exact_from_socket(client_socket, 4)
            if not length_bytes:
                return
            
            notification_length = int.from_bytes(length_bytes, byteorder='big')
            
            # Receive notification data
            notification_bytes = self.receive_exact_from_socket(client_socket, notification_length)
            if not notification_bytes:
                return
            
            notification = json.loads(notification_bytes.decode('utf-8'))
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
            
        except json.JSONDecodeError:
            print(f"\n❌ Failed to decode notification")
        except Exception as e:
            print(f"\n❌ Error handling notification: {str(e)}")
        finally:
            client_socket.close()

    def receive_exact_from_socket(self, sock, n):
        """Receive exactly n bytes from a specific socket"""
        data = b''
        while len(data) < n:
            try:
                packet = sock.recv(n - len(data))
                if not packet:
                    return None
                data += packet
            except Exception:
                return None
        return data

    def start(self):
        print("Welcome to the News Channel System! (TCP Version)")
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
                    # Start notification listener after successful registration
                    if self.is_authenticated and not self.receive_thread:
                        self.receive_thread = threading.Thread(target=self.receive_notifications)
                        self.receive_thread.daemon = True
                        self.receive_thread.start()
                        print("✅ Notification system ready!")
                elif cmd == "login" and len(args) == 2:
                    self.login(args[0], args[1])
                    # Start notification listener after successful login
                    if self.is_authenticated and not self.receive_thread:
                        self.receive_thread = threading.Thread(target=self.receive_notifications)
                        self.receive_thread.daemon = True
                        self.receive_thread.start()
                        print("✅ Notification system ready!")
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
        
        # Cleanup
        if self.sock:
            self.sock.close()
        if self.notification_sock:
            self.notification_sock.close()

if __name__ == "__main__":
    client = Client()
    client.start()
