import subprocess
import time
import sys

def start_process(cmd):
    return subprocess.Popen(
        cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1
    )

def send_command(proc, command):
    proc.stdin.write(command + '\n')
    proc.stdin.flush()

def read_until(proc, expected, timeout=5):
    import select
    start = time.time()
    output = ""
    while time.time() - start < timeout:
        ready, _, _ = select.select([proc.stdout], [], [], 0.1)
        if ready:
            line = proc.stdout.readline()
            if not line:
                continue
            print(f"[DEBUG] {line.strip()}")
            output += line
            if expected in line:
                return output
        else:
            time.sleep(0.1)
    return output

def main():
    # 1. Start server
    server = start_process([sys.executable, "server.py"])
    print("Server started.")
    time.sleep(1)

    # 2. Start Client 1 (publisher)
    client1 = start_process([sys.executable, "client.py"])
    print("Client 1 started.")
    read_until(client1, "Notification system ready!", 5)
    send_command(client1, 'list_channels')
    read_until(client1, "Available channels", 2)

    # 3. Start Client 2 (subscriber)
    client2 = start_process([sys.executable, "client.py"])
    print("Client 2 started.")
    read_until(client2, "Notification system ready!", 5)
    send_command(client2, 'list_channels')
    read_until(client2, "Available channels", 2)

    # 4. Client 1: create channel
    send_command(client1, 'create_channel "Tech" "Tech news"')
    out1 = read_until(client1, "Channel 'Tech' created", 3)
    print("Client 1 create_channel output:\n", out1)
    assert "Channel 'Tech' created" in out1, "Channel creation failed!"
    print("[PASS] Channel creation")

    # 5. Client 2: should receive notification about new channel
    notif2 = read_until(client2, "new_channel", 3)
    print("Client 2 notification for new channel:\n", notif2)
    assert "new_channel" in notif2, "Client 2 did not receive new_channel notification!"
    print("[PASS] New channel notification received by Client 2")

    # 6. Client 2: subscribe to channel
    send_command(client2, 'subscribe "Tech"')
    out2 = read_until(client2, "Subscribed to channel", 3)
    print("Client 2 subscribe output:\n", out2)
    assert "Subscribed to channel" in out2, "Client 2 failed to subscribe!"
    print("[PASS] Client 2 subscribed to channel")

    # 7. Client 1: publish news (allowed)
    send_command(client1, 'publish_news "Tech" "Breaking: New AI released!"')
    out1 = read_until(client1, "News published successfully", 3)
    print("Client 1 publish_news output:\n", out1)
    assert "News published successfully" in out1, "Client 1 failed to publish news!"
    print("[PASS] News published by Client 1")

    # 8. Client 2: should receive news notification
    notif2 = read_until(client2, "new_news", 3)
    print("Client 2 news notification:\n", notif2)
    assert "new_news" in notif2, "Client 2 did not receive news notification!"
    print("[PASS] Client 2 received news notification")

    # 9. Client 2: unsubscribe from channel
    send_command(client2, 'unsubscribe "Tech"')
    out2 = read_until(client2, "Unsubscribed from channel", 3)
    print("Client 2 unsubscribe output:\n", out2)
    assert "Unsubscribed from channel" in out2, "Client 2 failed to unsubscribe!"
    print("[PASS] Client 2 unsubscribed from channel")

    # 10. Client 1: publish news (should NOT be received by client 2)
    send_command(client1, 'publish_news "Tech" "Another update!"')
    out1 = read_until(client1, "News published successfully", 3)
    print("Client 1 publish_news output (after unsubscribe):\n", out1)
    assert "News published successfully" in out1, "Client 1 failed to publish news after unsubscribe!"
    notif2 = read_until(client2, "new_news", 2)
    print("Client 2 news notification after unsubscribe (should be empty):\n", notif2)
    assert "new_news" not in notif2, "Client 2 received news after unsubscribe!"
    print("[PASS] Client 2 did NOT receive news after unsubscribe")

    # 11. Client 1: publish forbidden news
    send_command(client1, 'publish_news "Tech" "This contains spam"')
    out1 = read_until(client1, "forbidden words", 3)
    print("Client 1 forbidden news output:\n", out1)
    assert "forbidden words" in out1, "Forbidden news was not blocked!"
    print("[PASS] Forbidden news blocked")

    # 12. Client 1: delete channel
    send_command(client1, 'delete_channel "Tech"')
    out1 = read_until(client1, "Channel 'Tech' deleted", 3)
    print("Client 1 delete_channel output:\n", out1)
    assert "Channel 'Tech' deleted" in out1, "Channel deletion failed!"
    print("[PASS] Channel deleted")

    # 13. Client 2: should receive notification about channel deletion
    notif2 = read_until(client2, "channel_deleted", 3)
    print("Client 2 channel_deleted notification:\n", notif2)
    assert "channel_deleted" in notif2, "Client 2 did not receive channel_deleted notification!"
    print("[PASS] Client 2 received channel_deleted notification")

    # Cleanup
    client1.terminate()
    client2.terminate()
    server.terminate()
    print("Test finished.")

if __name__ == "__main__":
    main()