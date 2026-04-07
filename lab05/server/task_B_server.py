import socket
import subprocess

HOST = '127.0.0.1'
PORT = 8999

def execute_command(command):
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, encoding="cp866")
        if result.stdout:
            return result.stdout
        elif result.stderr:
            return f"ERROR: {result.stderr}"
        else:
            return "Command executed successfully (no output)"
    except Exception as e:
        return f"Ошибка: {e}"

def start_server():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.bind((HOST, PORT))
        server_socket.listen(1)
        print(f"Server listening on {HOST}:{PORT}")

        while True:
            client_socket, client_address = server_socket.accept()
            print(f"Connected to {client_address}")

            with client_socket:
                data = client_socket.recv(4096).decode('utf-8')
                if not data:
                    break

                print(f"Received command: {data}")
                result = execute_command(data)
                client_socket.sendall(result.encode('utf-8'))
                print(f"Result sent to client")

if __name__ == "__main__":
    start_server()