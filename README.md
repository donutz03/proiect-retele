# News Channel Subscription System

## Overview

This is a client-server application implemented in Python using UDP sockets that allows clients to subscribe to and receive notifications for news channels.

## Features

### Server Features

- **Channel Management**: Manages news channels with names and descriptions
- **User Authentication**: Registration and login system
- **Content Filtering**: Blocks news containing predefined forbidden words
- **Subscription Management**: Handles client subscriptions to channels
- **Real-time Notifications**: Notifies clients about new channels, deleted channels, and news

### Client Features

- User registration and authentication
- View all available channels
- Create new news channels
- Delete owned channels
- Subscribe/unsubscribe to channels
- Publish news to owned channels
- Receive real-time notifications

## Forbidden Words

The server filters content and blocks news containing these words:

- spam
- hack
- virus
- malware
- phishing
- scam

## Usage

### Starting the Server

```bash
python server.py
```

### Starting the Client

```bash
python client.py
```

### Client Commands

#### Authentication

- `register <username> <password>` - Register a new user
- `login <username> <password>` - Login with existing credentials

#### Channel Management

- `list_channels` - Show all available channels
- `create_channel "<channel name>" "<description>"` - Create a new channel
- `delete_channel "<channel name>"` - Delete your own channel

#### Subscription Management

- `subscribe "<channel name>"` - Subscribe to a channel
- `unsubscribe "<channel name>"` - Unsubscribe from a channel
- `my_subscriptions` - Show your current subscriptions

#### News Publishing

- `publish_news "<channel name>" <news content>` - Publish news to your channel

#### Other

- `exit` - Exit the application

## System Architecture

### Channel Class

- Stores channel name, description, creator, and subscriber list
- Manages news messages and subscription operations

### Server Class

- Handles all client requests via UDP
- Manages user authentication and channel operations
- Implements content filtering for news
- Sends notifications to relevant clients

### Client Class

- Provides interactive command-line interface
- Handles communication with server
- Receives and displays real-time notifications

## Notification Types

1. **New Channel**: When a channel is created, all connected clients are notified
2. **Channel Deleted**: When a channel is deleted, all connected clients are notified
3. **New News**: When news is published, only subscribers to that channel are notified

## Example Usage Flow

1. **Start Server**: `python server.py`
2. **Start Multiple Clients**: `python client.py` (in separate terminals)
3. **Register Users**: `register alice password123`
4. **Login**: `login alice password123`
5. **Create Channel**: `create_channel "Tech News" "Latest technology updates"`
6. **Subscribe**: `subscribe "Tech News"`
7. **Publish News**: `publish_news "Tech News" New smartphone released with amazing features`
8. **View Subscriptions**: `my_subscriptions`

## Requirements Met

✅ **Server manages channels with names and descriptions**
✅ **Clients receive channel list upon connection**
✅ **Clients can publish channels with server notification to all clients**
✅ **Clients can delete owned channels with server notification**
✅ **Clients can subscribe to channels for notifications**
✅ **Clients can unsubscribe from channels**
✅ **Channel creators can publish news to subscribers**
✅ **Server filters content and blocks forbidden words**

## Technical Details

- **Protocol**: UDP with JSON message format
- **Threading**: Server uses threading for notifications
- **Port Management**: Dynamic notification port assignment
- **Error Handling**: Comprehensive error handling and validation
- **Content Security**: Real-time content filtering system
