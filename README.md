# Secure Chat Application with File Transfer

This is a secure chat application implemented in Python that allows multiple users to communicate with each other over a server. The application uses SSL/TLS for encrypted communication and supports basic functionalities like sending text messages, transferring files, listing active users, and performing administrative actions such as banning or kicking users.

## Features

- **SSL Encryption:** The chat is secure with SSL/TLS encryption.
- **Multi-client Support:** Multiple clients can connect to the server simultaneously.
- **User Nickname System:** Clients choose a nickname upon connection.
- **Active Users List:** Clients can request a list of currently connected users.
- **File Transfer:** Users can send files to each other via the `/file` command.
- **Admin Commands:** The server admin can kick or ban users by nickname.
- **Logging:** All messages and actions are logged in a history file.
- **Ban List:** Banned users are prevented from reconnecting until the ban is lifted.

## Requirements

- Python 3.x
- SSL certificates (`server-cert.pem` and `server-key.pem`) for encrypted communication.

## Commands
Client Commands
/file <filename> <recipient_nickname>: Send a file to another user.
/users: List all active users on the server.
/quit: Disconnect from the server.
Admin Commands (Server-side)
/kick <nickname>: Kick a user from the server.
/ban <nickname>: Ban a user from the server. Banned users cannot reconnect.
## File Transfer
Users can send files to one another using the /file command. The recipient will receive the file in the Received directory on their local machine.
