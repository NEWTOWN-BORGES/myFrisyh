import socket
import threading
import argparse
import json # Necessário para lidar com mensagens JSON
import uuid # Para gerar task_ids, embora create_task_message já faça isso

# Importar funções do message_formats.py
from message_formats import create_task_message, create_result_message, parse_message

class P2PNode:
    def __init__(self, host, port, initial_peers=None):
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) # Allow address reuse
        self.peers = [] # List to store connected peer sockets
        self.lock = threading.Lock() # Lock for thread-safe access to self.peers

        if initial_peers is None:
            initial_peers = []

        # Connect to initial peers
        for peer_host, peer_port in initial_peers:
            self.connect_to_peer(peer_host, int(peer_port))

    def start_listening(self):
        """
        Starts a thread to listen for incoming connections.
        """
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        print(f"[*] Listening on {self.host}:{self.port}")

        thread = threading.Thread(target=self._accept_connections, daemon=True)
        thread.start()

    def _accept_connections(self):
        """
        Accepts incoming connections and starts a new thread to handle each one.
        This method is intended to be run in a separate thread.
        """
        while True:
            try:
                client_socket, client_address = self.server_socket.accept()
                print(f"[+] Accepted connection from {client_address[0]}:{client_address[1]}")
                with self.lock:
                    self.peers.append(client_socket)

                # Start a new thread to handle messages from this peer
                peer_thread = threading.Thread(target=self.handle_peer_messages, args=(client_socket,), daemon=True)
                peer_thread.start()
            except socket.error as e: # Mais específico para erros de socket
                print(f"[!] Socket error accepting connections: {e}")
                # Considerar se deve quebrar o loop ou apenas logar o erro e continuar
                # Por enquanto, manter o break para evitar loops infinitos em certos erros.
                break
            except Exception as e:
                print(f"[!] Unexpected error accepting connections: {e}")
                break # Exit loop on unexpected error

    def connect_to_peer(self, peer_host, peer_port):
        """
        Connects to a peer at the specified host and port.
        """
        try:
            peer_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            peer_socket.connect((peer_host, peer_port))
            print(f"[*] Connected to {peer_host}:{peer_port}")
            with self.lock:
                self.peers.append(peer_socket)

            # Start a new thread to handle messages from this peer
            peer_thread = threading.Thread(target=self.handle_peer_messages, args=(peer_socket,), daemon=True)
            peer_thread.start()
            return True
        except socket.error as e:
            print(f"[!] Failed to connect to {peer_host}:{peer_port}. Error: {e}")
            return False

    def handle_peer_messages(self, peer_socket):
        """
        Listens for messages from a given peer socket and handles them.
        """
        while True:
            try:
                data = peer_socket.recv(1024)
                if not data:
                    # Connection closed by peer
                    print(f"[-] Peer {peer_socket.getpeername()} disconnected.")
                    with self.lock:
                        if peer_socket in self.peers:
                            self.peers.remove(peer_socket)
                    peer_socket.close()
                    break

                message_str = data.decode('utf-8')
                parsed_msg = parse_message(message_str)
                peer_address_tuple = peer_socket.getpeername()
                peer_address = f"{peer_address_tuple[0]}:{peer_address_tuple[1]}"

                if parsed_msg:
                    msg_type = parsed_msg.get("type")
                    if msg_type == "task":
                        task_id = parsed_msg.get("task_id")
                        operation = parsed_msg.get("operation")
                        task_data = parsed_msg.get("data")
                        print(f"\n[TASK_RECV] From {peer_address}: Task ID {task_id}, Op: {operation}, Data: {task_data}")

                        if operation == "sum":
                            if isinstance(task_data, list) and len(task_data) == 2:
                                try:
                                    num1 = float(task_data[0])
                                    num2 = float(task_data[1])
                                    result_value = num1 + num2
                                    print(f"[TASK_PROC] Task {task_id}: {num1} + {num2} = {result_value}")
                                    result_msg_str = create_result_message(task_id, result_value)
                                    self.send_message_to_peer(peer_socket, result_msg_str)
                                    print(f"[RESULT_SENT] To {peer_address} for Task ID {task_id}")
                                except (ValueError, TypeError) as e:
                                    print(f"[!] Error processing 'sum' task {task_id}: Invalid data format - {e}")
                                    error_msg_str = create_result_message(task_id, None, f"Invalid data for sum: {task_data}")
                                    self.send_message_to_peer(peer_socket, error_msg_str)
                            else:
                                print(f"[!] Error processing 'sum' task {task_id}: Data must be a list of two numbers.")
                                error_msg_str = create_result_message(task_id, None, "Invalid data for sum operation, expected list of two numbers.")
                                self.send_message_to_peer(peer_socket, error_msg_str)
                        else:
                            print(f"[!] Unknown operation '{operation}' for task {task_id}.")
                            error_msg_str = create_result_message(task_id, None, f"Unknown operation: {operation}")
                            self.send_message_to_peer(peer_socket, error_msg_str)

                    elif msg_type == "result":
                        task_id = parsed_msg.get("task_id")
                        value = parsed_msg.get("value")
                        error = parsed_msg.get("error")
                        print(f"\n[RESULT_RECV] From {peer_address}: Task ID {task_id}, Value: {value}, Error: {error}")

                    elif msg_type == "generic_text": # Handling plain text messages separately
                        text_content = parsed_msg.get("content", "")
                        print(f"\n[MSG_RECV] Text from {peer_address}: {text_content}")

                    else:
                        print(f"\n[!] Received unknown message type '{msg_type}' from {peer_address}: {message_str}")
                else:
                    # If parse_message returns None, it might be a plain text message or malformed JSON
                    # For backward compatibility or simple text chat, we can assume it's a plain text message if it doesn't parse.
                    # However, the new design emphasizes JSON messages.
                    # For now, let's log it as a potential issue if it's not explicitly a "generic_text" type message.
                    # A better approach would be to wrap plain text in a JSON structure too.
                    # For this iteration, let's assume non-JSON is an error or an old format.
                    print(f"\n[!] Received malformed JSON or non-JSON message from {peer_address}: {message_str}")

            except socket.error as e:
                # Existing error handling for socket issues
                print(f"[!] Socket error with {peer_socket.getpeername() if peer_socket.fileno() != -1 else 'disconnected peer'}: {e}")
                with self.lock:
                    if peer_socket in self.peers:
                        self.peers.remove(peer_socket)
                if peer_socket.fileno() != -1:
                    peer_socket.close()
                break
            except json.JSONDecodeError as e: # Specifically catch JSON decoding errors if parse_message raises it
                peer_address_tuple = peer_socket.getpeername() if peer_socket.fileno() != -1 else ('unknown', 0)
                peer_address = f"{peer_address_tuple[0]}:{peer_address_tuple[1]}"
                print(f"\n[!] Failed to decode JSON from {peer_address}: {e}. Data: '{data.decode('utf-8', errors='ignore')}'")
                # No need to remove peer here unless this is a frequent or malicious issue.
            except Exception as e: # Catch other potential errors
                peer_address_tuple = peer_socket.getpeername() if peer_socket.fileno() != -1 else ('unknown', 0)
                peer_address = f"{peer_address_tuple[0]}:{peer_address_tuple[1]}"
                print(f"[!] Unexpected error handling message from {peer_address}: {e}")
                # Optionally, break or handle more gracefully
                break


    def send_message_to_peer(self, peer_socket, message_str_json): # Expects a JSON string
        """
        Sends a JSON string message to a specific peer.
        """
        try:
            peer_socket.sendall(message_str_json.encode('utf-8'))
        except socket.error as e:
            print(f"[!] Error sending message to {peer_socket.getpeername() if peer_socket.fileno() != -1 else 'disconnected peer'}: {e}")
            with self.lock:
                if peer_socket in self.peers:
                    self.peers.remove(peer_socket)
            if peer_socket.fileno() != -1:
                peer_socket.close()


    def broadcast_message(self, message_str_json): # Expects a JSON string
        """
        Sends a JSON string message to all connected peers.
        """
        # No direct print here, sending function will confirm or error
        # print(f"[*] Broadcasting message: {message_str_json}")
        with self.lock:
            for peer_socket in list(self.peers):
                try:
                    self.send_message_to_peer(peer_socket, message_str_json)
                except Exception as e: # Should be caught by send_message_to_peer, but as a safeguard
                    print(f"[!] Error broadcasting to a peer (socket: {peer_socket.fileno()}): {e}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="P2P Node with Task/Result Exchange")
    parser.add_argument('port', type=int, help="Port for the node to listen on")
    parser.add_argument('--host', type=str, default='0.0.0.0', help="Host for the node to listen on (default: 0.0.0.0)")
    parser.add_argument('--peers', type=str, help="Comma-separated list of initial peers to connect to (e.g., 127.0.0.1:8001,127.0.0.1:8002)")

    args = parser.parse_args()

    initial_peer_list = []
    if args.peers:
        peers_str = args.peers.split(',')
        for peer_addr in peers_str:
            try:
                host, port_str = peer_addr.split(':')
                initial_peer_list.append((host, int(port_str)))
            except ValueError:
                print(f"[!] Invalid peer format: {peer_addr}. Skipping.")

    # Create and start the P2P node
    node = P2PNode(args.host, args.port, initial_peer_list)
    node.start_listening()

    print("\nNode started. Type 'quit' to exit.")
    print("Commands:")
    print("  task sum <num1> <num2>  (e.g., task sum 5 3)")
    print("  text <your_message>     (e.g., text Hello everyone!)")
    print("  (or just type your message for backward compatibility - will be wrapped as generic_text)")


    try:
        while True:
            raw_input_message = input("> ")
            if raw_input_message.lower() == 'quit':
                break

            if not raw_input_message:
                continue

            parts = raw_input_message.split()
            command = parts[0].lower()

            if command == "task" and len(parts) >= 4:
                op_name = parts[1].lower()
                try:
                    data_args = [float(p) for p in parts[2:]] # Convert data parts to float
                    if op_name == "sum" and len(data_args) == 2:
                        # task_id will be generated by create_task_message
                        task_msg_str = create_task_message(operation=op_name, data=data_args)
                        print(f"[*] Broadcasting TASK: {task_msg_str}")
                        node.broadcast_message(task_msg_str)
                    else:
                        print(f"[!] Invalid task format. For sum, use: task sum <num1> <num2>. Got: {raw_input_message}")
                except ValueError:
                    print(f"[!] Invalid data for task. Numbers expected. Got: {parts[2:]}")

            elif command == "text" and len(parts) > 1:
                text_content = " ".join(parts[1:])
                # Wrap plain text in a JSON structure for consistency
                generic_msg_dict = {"type": "generic_text", "content": text_content}
                generic_msg_str = json.dumps(generic_msg_dict)
                print(f"[*] Broadcasting TEXT: {generic_msg_str}")
                node.broadcast_message(generic_msg_str)

            else: # For backward compatibility or simple messages, wrap as generic_text
                # This allows old nodes or simple text to still be somewhat processed
                # Or, you could choose to disallow non-command inputs.
                print(f"[*] Wrapping as generic text and broadcasting: {raw_input_message}")
                generic_msg_dict = {"type": "generic_text", "content": raw_input_message}
                generic_msg_str = json.dumps(generic_msg_dict)
                node.broadcast_message(generic_msg_str)

    except KeyboardInterrupt:
        print("\n[*] Shutting down node...")
    finally:
        print("[*] Closing server socket...")
        if node.server_socket:
            node.server_socket.close()

        # Attempt to close all peer sockets gracefully
        print("[*] Closing peer connections...")
        with node.lock:
            for peer_sock in node.peers:
                try:
                    peer_sock.shutdown(socket.SHUT_RDWR) # Signal no more send/receive
                    peer_sock.close()
                except socket.error:
                    pass # Ignore errors if socket already closed or problematic
        print("[*] Node shut down.")
