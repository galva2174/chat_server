import socket
import threading
import shutil
import os
import ssl

initial_users = []

def receive():
    global initial_users
    while True:
        try:
            message = secure_client.recv(1024).decode('ascii')
            if not message:
                print("Connection closed by the server.")
                break

            if message.startswith('KICKED'):
                print("You have been kicked from the server by the admin.")
                secure_client.close()
                break
            elif message.startswith('BANNED'):
                print("You have been banned from the server by the admin.")
                secure_client.close()
                break
            elif message.startswith('INITIAL_USERS'):
                initial_users = message.split(' ')[1:]
                list_users(initial_users)   
            else:
                print(message)
        except Exception as e:
            print(f"An error occurred: {e}")
            break

def write():
    while True:
        try:
            message = input(' ')
            encoded_message = message.encode('ascii')

            if message.startswith('/file '):
                send_file(message)
            elif message.startswith('/users'):
                secure_client.send(encoded_message)
            else:
                secure_client.send(encoded_message)
        except Exception as e:
            print(f"An error occurred: {e}")
            break

def list_users(initial_users):
    print("-" * 50)
    print("Users on the server:")
    for user in initial_users:
        print(f"- {user}")
    print("-" * 50)

def choose_nickname():
    while True:
        new_nickname = input("Choose your nickname: ")
        secure_client.send(new_nickname.encode('ascii'))

        response = secure_client.recv(1024).decode('ascii')

        if response == 'NICK_IN_USE':
            print("The nickname is already in use. Please choose a different one.")
        elif response.startswith('INITIAL_USERS'):
            initial_users = response.split(' ')[1:]
            list_users(initial_users)
            break
        else:
            break

    return new_nickname

def send_file(command):
    _, filename, recipient_nickname = command.split(' ', 2)
    file_path = os.path.join(os.getcwd(), filename)

    active_users = read_user_list()

    if recipient_nickname not in active_users:
        print(f"Error: Nickname '{recipient_nickname}' is not on the server.")
        return

    with open(file_path, 'rb') as file:
        transfer_command = f'/file {recipient_nickname} {filename}'.encode('ascii')
        print(f"Sending file transfer command: {transfer_command}")
        secure_client.sendall(transfer_command)

        shutil.copyfileobj(file, secure_client.makefile('wb'))

        secure_client.sendall(b'<<END_OF_FILE>>')
        print(f"File transfer complete")

def read_user_list():
    try:
        user_list_path = os.path.join('Active Users', 'user_list.txt')
        with open(user_list_path, 'r') as user_list_file:
            return user_list_file.read().splitlines()
    except FileNotFoundError:
        return []


if __name__ == "__main__":
    server_ip = '127.0.0.1'
    server_hostname = 'vishwaas'

    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    ssl_context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
    ssl_context.load_verify_locations('server-cert.pem')

    secure_client = ssl_context.wrap_socket(client, server_hostname=server_hostname)

    try:
        secure_client.connect((server_ip, 55555))
    except Exception as e:
        print(f"Connection error: {e}")
        exit()

    initial_users = read_user_list()
    choose_nickname()

    receive_thread = threading.Thread(target=receive)
    receive_thread.start()

    write_thread = threading.Thread(target=write)
    write_thread.start()
