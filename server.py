import socket
import ssl
import threading
import os
import getpass
import datetime

clients = []
nicknames = []
banned_nicknames = set()

def handle(client, nickname):
    try:
        while True:
            data = client.recv(1024)
            if not data:
                break

            message = data.decode('ascii')

            if message.startswith('/quit'):
                break
            elif message.startswith('/file'):
                handle_file_transfer(message, client, nickname)
            elif message.startswith('/users'):
                print_active_users(client, nickname)
            else:
                log(message, nickname)
                broadcast(message.encode('ascii'), nickname)
    except Exception as e:
        log(f"Error handling message from {nickname}: {e}")
    finally:
        remove_client(client, nickname)

def print_active_users(client, nickname):
    active_users = "\nActive Users:\n" + "\n".join(nicknames) + "\n"
    client.sendall(active_users.encode('ascii'))
    log(f'{nickname} printed the active users')

def broadcast(message, sender_nickname):
    for client, client_nickname in clients:
        if client_nickname != sender_nickname:
            try:
                if message.decode('ascii').startswith('/file'):
                    client.sendall(message)
                else:
                    message_to_send = f"{sender_nickname} - {message.decode('ascii')}"
                    client.sendall(message_to_send.encode('ascii'))

                update_user_list_file()
            except Exception as e:
                log(f"Error broadcasting message to {client_nickname}: {e}")
                remove_client(client, client_nickname)

def log(message, sender_nickname=None):
    if sender_nickname is None:
        log_entry = f" {message}"
    else:
        log_entry = f"{sender_nickname} - {message}"

    print(log_entry)

    start_date = datetime.datetime.now().strftime("%d-%m-%Y")
    history_file_name = f"History_Date_{start_date}.txt"
    history_folder_path = os.path.join(os.getcwd(), 'History')
    os.makedirs(history_folder_path, exist_ok=True)

    history_file_path = os.path.join(history_folder_path, history_file_name)
    with open(history_file_path, 'a') as history_file:
        history_file.write(log_entry + '\n')

def update_user_list_file():
    try:
        with open('Active Users/user_list.txt', 'r') as user_list_file:
            existing_users = user_list_file.read().splitlines()
    except FileNotFoundError:
        existing_users = []

    updated_user_list = list(set(existing_users + nicknames))

    active_users_folder_path = os.path.join(os.getcwd(), 'Active Users')
    os.makedirs(active_users_folder_path, exist_ok=True)

    with open(os.path.join(active_users_folder_path, 'user_list.txt'), 'w') as user_list_file:
        user_list_file.write("\n".join(updated_user_list))

def admin_command(message):
    if message.startswith('/kick '):
        target_nickname = message.split(' ')[1]
        for target_client, target_client_nickname in clients:
            if target_client_nickname == target_nickname:
                remove_client(target_client, target_client_nickname)
                broadcast(f' was kicked by the admin!'.encode('ascii'), target_client_nickname)
                break
    elif message.startswith('/ban '):
        target_nickname = message.split(' ')[1]
        ban_user(target_nickname)

def ban_user(nickname):
    global nicknames
    global clients
    global banned_nicknames

    if nickname not in nicknames:
        print(f"Error: Nickname '{nickname}' not found.")
    else:
        index = nicknames.index(nickname)

        if index < len(clients):
            client, _ = clients.pop(index)
            client.send('BANNED'.encode('ascii'))
            client.close()
            ban_message = f'{nickname} was banned by the admin!'
            print(ban_message)
            broadcast(ban_message.encode('ascii'), nickname)

            nicknames.remove(nickname)
            update_user_list_file()
            user_list_file_path = os.path.join(os.getcwd(), 'Active Users', 'user_list.txt')
            try:
                with open(user_list_file_path, 'r') as user_list_file:
                    existing_users = user_list_file.read().splitlines()
            except FileNotFoundError:
                existing_users = []

            updated_user_list = list(filter(lambda user: user != nickname, existing_users))

            with open(user_list_file_path, 'w') as user_list_file:
                user_list_file.write("\n".join(updated_user_list))

            broadcast(f'USER_LIST_UPDATE {" ".join(nicknames)}'.encode('ascii'), nickname)

            bans_folder_path = os.path.join(os.getcwd(), 'bans')
            os.makedirs(bans_folder_path, exist_ok=True)

            banlist_file_path = os.path.join(bans_folder_path, 'banlist.txt')
            with open(banlist_file_path, 'a') as banlist_file:
                banlist_file.write(f"{nickname}\n")

        else:
            print(f"Error: Index {index} out of range.")

def handle_file_transfer(command, client, sender_nickname):
    _, recipient_nickname, filename = command.split(' ', 2)

    received_folder_path = os.path.join('Received', recipient_nickname)
    os.makedirs(received_folder_path, exist_ok=True)

    file_path = os.path.join(received_folder_path, filename)

    try:
        with open(file_path, 'wb') as file:
            while True:
                data = client.recv(1024)
                if not data or data == b'<<END_OF_FILE>>':
                    break
                file.write(data)
            log(f'{filename} sent from {sender_nickname} to {recipient_nickname}')
            # recipient_nickname.send(f"File '{filename}' received from {sender_nickname}".encode('ascii'))
            broadcast(f"sent a file {filename} to you".encode('ascii'),sender_nickname)
    except Exception as e:
        log(f"Error handling file transfer: {e}")

def remove_client(client_to_remove, nickname_to_remove):
    try:
        clients_copy = clients.copy()

        for client, nickname in clients_copy:
            if client == client_to_remove and nickname == nickname_to_remove:
                clients.remove((client, nickname))
                client_to_remove.close()

                broadcast(f' disconnected'.encode('ascii'), nickname_to_remove)
                log(f"{nickname_to_remove} disconnected")

                if nickname_to_remove in nicknames:
                    nicknames.remove(nickname_to_remove)
                    update_user_list_file()

                    user_list_file_path = os.path.join(os.getcwd(), 'Active Users', 'user_list.txt')
                    try:
                        with open(user_list_file_path, 'r') as user_list_file:
                            existing_users = user_list_file.read().splitlines()
                    except FileNotFoundError:
                        existing_users = []

                    updated_user_list = list(filter(lambda user: user != nickname_to_remove, existing_users))

                    with open(user_list_file_path, 'w') as user_list_file:
                        user_list_file.write("\n".join(updated_user_list))

                break

    except Exception as e:
        print(f"Error removing client ({client_to_remove}, {nickname_to_remove}): {e}")

# ...

def receive_connections():
    load_banlist()
    while True:
        client_socket, address = server.accept()

        try:
            context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            context.load_cert_chain(certfile='server-cert.pem', keyfile='server-key.pem')
            secure_client = context.wrap_socket(client_socket, server_side=True)
            secure_client.send('success'.encode('ascii'))

            while True:
                nickname = secure_client.recv(1024).decode('ascii')

                if is_nickname_unique(nickname) and not is_banned(nickname):
                    nicknames.append(nickname)
                    clients.append((secure_client, nickname))

                    log("{} joined Chat!".format(nickname))
                    log("Connected with {}".format(str(address)))
                    log("-" * 50)
                    secure_client.send(f'INITIAL_USERS {" ".join(nicknames)}'.encode('ascii'))  # Send the initial user list
                    broadcast(" joined!".format(nickname).encode('ascii'), nickname)
                    update_user_list_file()

                    thread = threading.Thread(target=handle, args=(secure_client, nickname))
                    thread.start()
                    break
                else:
                    secure_client.send('You are banned'.encode('ascii'))
                    new_nickname = secure_client.recv(1024).decode('ascii')
                    if is_nickname_unique(new_nickname) and not is_banned(new_nickname):
                        nicknames.append(new_nickname)
                        clients.append((secure_client, new_nickname))
                        log(f"Nickname changed to {new_nickname}")
                        secure_client.send(f'INITIAL_USERS {" ".join(nicknames)}'.encode('ascii'))
                        log("Connected with {}".format(str(address)))
                        log("-" * 50)
                        update_user_list_file()

                        thread = threading.Thread(target=handle, args=(secure_client, new_nickname))
                        thread.start()
                        break
                    else:
                        secure_client.send('NICK_IN_USE'.encode('ascii'))

        except Exception as e:
            log(f"Error during connection setup: {e}")

# ...

def is_banned(nickname):
    return nickname in banned_nicknames

# ...

def is_nickname_unique(nickname):
    return nickname not in nicknames and nickname not in banned_nicknames

def load_banlist():
    bans_folder_path = os.path.join(os.getcwd(), 'Bans')
    os.makedirs(bans_folder_path, exist_ok=True)

    banlist_file_path = os.path.join(bans_folder_path, 'banlist.txt')

    try:
        with open(banlist_file_path, 'r') as banlist_file:
            banned_nicknames.update(line.strip() for line in banlist_file)
    except FileNotFoundError:
        with open(banlist_file_path, 'w') as banlist_file:
            pass


def start_server():
    global server
    host = '127.0.0.1'  # Use the loopback address
    port = 55555

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((host, port))
    server.listen()

    log(f"Server listening on {host}:{port}")
    log("-" * 100)

    receive_thread = threading.Thread(target=receive_connections)
    receive_thread.start()

    while True:
        message = input()
        admin_command(message)

if __name__ == "__main__":
    start_server()
