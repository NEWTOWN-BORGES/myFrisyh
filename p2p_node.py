import socket
import threading
import argparse
import json # Necessário para lidar com mensagens JSON
import uuid # Para gerar task_ids

# Importações de message_formats são feitas localmente nos métodos ou no if __name__

class P2PNode:
    def __init__(self, host, port, initial_peers=None):
        self.host = host
        self.port = port
        self.node_id = f"{self.host}:{self.port}"
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.peers = []
        self.lock = threading.Lock() # Lock para self.peers

        self.offered_tasks = {}
        self.processing_tasks = {} # Tarefas que este nó está processando para outros
        self.task_pool_lock = threading.Lock()

        if initial_peers is None:
            initial_peers = []
        for peer_host, peer_port_val in initial_peers:
            self.connect_to_peer(peer_host, int(peer_port_val))

    def start_listening(self):
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        print(f"[*] Listening on {self.node_id}")
        threading.Thread(target=self._accept_connections, daemon=True).start()

    def _accept_connections(self):
        while True:
            try:
                client_socket, client_address = self.server_socket.accept()
                peer_id = f"{client_address[0]}:{client_address[1]}"
                print(f"[+] Accepted connection from {peer_id}")
                with self.lock:
                    self.peers.append(client_socket)
                threading.Thread(target=self.handle_peer_messages, args=(client_socket,), daemon=True).start()
            except socket.error as e:
                print(f"[!] Socket error accepting connections: {e}")
                break
            except Exception as e:
                print(f"[!] Unexpected error accepting connections: {e}")
                break

    def connect_to_peer(self, peer_host, peer_port):
        try:
            peer_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            peer_socket.connect((peer_host, peer_port))
            peer_id = f"{peer_host}:{peer_port}"
            print(f"[*] Connected to {peer_id}")
            with self.lock:
                self.peers.append(peer_socket)
            threading.Thread(target=self.handle_peer_messages, args=(peer_socket,), daemon=True).start()
            return True
        except socket.error as e:
            print(f"[!] Failed to connect to {peer_host}:{peer_port}. Error: {e}")
            return False

    def _get_peer_id(self, peer_socket_or_address_tuple):
        if isinstance(peer_socket_or_address_tuple, socket.socket):
            try:
                peer_address_tuple = peer_socket_or_address_tuple.getpeername()
                return f"{peer_address_tuple[0]}:{peer_address_tuple[1]}"
            except socket.error: # pragma: no cover
                return "unknown_peer_socket"
        elif isinstance(peer_socket_or_address_tuple, tuple) and len(peer_socket_or_address_tuple) == 2:
            return f"{peer_socket_or_address_tuple[0]}:{peer_socket_or_address_tuple[1]}"
        return "unknown_peer_format" # pragma: no cover


    def is_idle(self) -> bool:
        """Verifica se o nó está atualmente processando alguma tarefa."""
        with self.task_pool_lock:
            if not self.processing_tasks:
                return True
            for task_info in self.processing_tasks.values():
                if task_info.get('status') == 'processing':
                    return False
            return True

    def handle_peer_messages(self, peer_socket):
        peer_id = self._get_peer_id(peer_socket)
        from message_formats import (parse_message, create_task_message,
                                     create_result_message, create_no_task_available_message,
                                     create_announce_task_message, create_request_task_message)
        while True:
            try:
                data = peer_socket.recv(1024)
                if not data: # pragma: no cover (difícil de testar desconexão controlada em simulação)
                    print(f"[-] Peer {peer_id} disconnected.")
                    with self.lock:
                        if peer_socket in self.peers: self.peers.remove(peer_socket)
                    if peer_socket.fileno() != -1: peer_socket.close()
                    break

                message_str = data.decode('utf-8')
                parsed_msg = parse_message(message_str)

                if parsed_msg:
                    msg_type = parsed_msg.get("type")

                    if msg_type == "task":
                        task_id = parsed_msg.get("task_id")
                        operation = parsed_msg.get("operation")
                        task_data = parsed_msg.get("data")
                        assigned_to_worker = parsed_msg.get("assigned_to")

                        if assigned_to_worker and assigned_to_worker != self.node_id:
                            continue

                        print(f"\n[TASK_ASSIGNED_TO_ME] From {peer_id} for me ({self.node_id}): Task ID {task_id}, Op: {operation}")

                        with self.task_pool_lock:
                            if task_id in self.processing_tasks and self.processing_tasks[task_id]['status'] == 'processing':
                                print(f"  [INFO] Task {task_id} is already being processed. Ignoring duplicate assignment.")
                                continue
                            self.processing_tasks[task_id] = {
                                'operation': operation, 'data': task_data,
                                'requested_from': peer_id,
                                'status': 'processing'
                            }

                        if operation == "sum":
                            if isinstance(task_data, list) and len(task_data) >= 1:
                                try:
                                    float_data = [float(x) for x in task_data]
                                    result_value = sum(float_data)
                                    print(f"  [TASK_PROC_WORKER] Node {self.node_id} processing Task {task_id}: sum({float_data}) = {result_value}")
                                    result_msg_str = create_result_message(task_id, result_value)
                                    self.send_message_to_peer(peer_socket, result_msg_str)
                                    print(f"  [RESULT_SENT_WORKER] Node {self.node_id} sent result for Task {task_id} to {peer_id}")
                                    with self.task_pool_lock:
                                        if task_id in self.processing_tasks:
                                            del self.processing_tasks[task_id]
                                except Exception as e:
                                    err_msg = f"Error during sum operation for task {task_id}: {e}"
                                    print(f"  [!] {self.node_id}: {err_msg}")
                                    error_msg_str = create_result_message(task_id, None, err_msg)
                                    self.send_message_to_peer(peer_socket, error_msg_str)
                                    with self.task_pool_lock:
                                        if task_id in self.processing_tasks: del self.processing_tasks[task_id]
                            else:
                                err_msg = "Data for sum must be a list of at least one number."
                                print(f"  [!] Error processing 'sum' task {task_id} by {self.node_id}: {err_msg}")
                                error_msg_str = create_result_message(task_id, None, err_msg)
                                self.send_message_to_peer(peer_socket, error_msg_str)
                                with self.task_pool_lock:
                                     if task_id in self.processing_tasks: del self.processing_tasks[task_id]
                        else:
                            err_msg = f"Unknown operation '{operation}' for task {task_id}."
                            print(f"  [!] {self.node_id}: {err_msg}")
                            error_msg_str = create_result_message(task_id, None, err_msg)
                            self.send_message_to_peer(peer_socket, error_msg_str)
                            with self.task_pool_lock:
                                if task_id in self.processing_tasks: del self.processing_tasks[task_id]

                    elif msg_type == "result":
                        res_task_id = parsed_msg.get("task_id")
                        res_value = parsed_msg.get("value")
                        res_error = parsed_msg.get("error")
                        with self.task_pool_lock:
                            if res_task_id in self.offered_tasks:
                                task_details = self.offered_tasks[res_task_id]
                                if task_details['status'] == 'pending':
                                    task_details['status'] = 'completed'
                                    task_details['result'] = {'value': res_value, 'error': res_error}
                                    worker_id_assigned = task_details.get('assigned_to', 'unknown worker')
                                    print(f"\n[RESULT_RECV_FOR_OFFERED_TASK] Task {res_task_id} (offered by me, {self.node_id}) completed by {worker_id_assigned} (via {peer_id}). Value={res_value}, Error={res_error}.")
                                else:
                                    print(f"\n[WARN_RESULT] Received result for offered task {res_task_id} from {peer_id}, but status was '{task_details['status']}', not 'pending'. Discarding.")
                            else:
                                print(f"\n[WARN_RESULT] Received result for a task ({res_task_id}) not in offered_tasks of node {self.node_id}, from {peer_id}. Discarding.")

                    elif msg_type == "request_task":
                        worker_requesting_id = parsed_msg.get("worker_id", peer_id)
                        print(f"\n[TASK_REQUEST_RECV] From worker {worker_requesting_id} (connection: {peer_id}) for a task.")
                        assigned_task_package = None
                        with self.task_pool_lock:
                            for current_task_id_iter, task_info_iter in self.offered_tasks.items():
                                if task_info_iter['status'] == 'available':
                                    task_info_iter['status'] = 'pending'
                                    task_info_iter['assigned_to'] = worker_requesting_id
                                    assigned_task_package = task_info_iter.copy()
                                    assigned_task_package['task_id'] = current_task_id_iter
                                    break
                        if assigned_task_package:
                            assign_msg_str = create_task_message(
                                operation=assigned_task_package['operation'], data=assigned_task_package['data'],
                                task_id=assigned_task_package['task_id'], assigned_to=worker_requesting_id
                            )
                            self.send_message_to_peer(peer_socket, assign_msg_str)
                            print(f"  [TASK_SENT_TO_WORKER] Task {assigned_task_package['task_id']} sent to worker {worker_requesting_id} (connection: {peer_id}).")
                        else:
                            no_task_msg_str = create_no_task_available_message(requester_node_id=self.node_id)
                            self.send_message_to_peer(peer_socket, no_task_msg_str)
                            print(f"  [NO_TASK_FOR_WORKER] No tasks currently available from {self.node_id} for worker {worker_requesting_id}. Sent NO_TASK_AVAILABLE.")

                    elif msg_type == "announce_task":
                        announcer_node_id = parsed_msg.get("node_id", peer_id)
                        task_count = parsed_msg.get("task_count", 0)
                        print(f"\n[TASK_ANNOUNCEMENT_RECV] Node {announcer_node_id} (conn: {peer_id}) announced {task_count} task(s).")
                        if self.node_id == announcer_node_id:
                            pass
                        elif self.is_idle() and task_count > 0:
                            print(f"  [WORKER_ACTION] Node {self.node_id} is idle and tasks are available. Requesting task from {announcer_node_id}.")
                            request_msg = create_request_task_message(worker_id=self.node_id)
                            self.send_message_to_peer(peer_socket, request_msg)
                        elif not self.is_idle():
                            print(f"  [WORKER_INFO] Node {self.node_id} is busy, not requesting task from {announcer_node_id} now.")
                        else:
                             print(f"  [WORKER_INFO] Node {announcer_node_id} has no tasks currently, not requesting.")


                    elif msg_type == "no_task_available":
                        task_host_node_id = parsed_msg.get("requester_node_id", peer_id)
                        print(f"\n[NO_TASK_INFO_RECV] Received NO_TASK_AVAILABLE from {task_host_node_id} (conn: {peer_id}). Will not request task from them now.")

                    elif msg_type == "generic_text":
                        content = parsed_msg.get("content", "")
                        sender = parsed_msg.get("sender", peer_id)
                        print(f"\n[MSG_RECV] Text from {sender} (via {peer_id}): {content}")

                    else: # pragma: no cover
                        print(f"\n[!] Received unknown message type '{msg_type}' from {peer_id}: {message_str[:200]}")
                else: # pragma: no cover
                    print(f"\n[!] Received malformed JSON from {peer_id}: {message_str[:200]}")

            except socket.error as e: # pragma: no cover
                peer_id_on_error = self._get_peer_id(peer_socket)
                print(f"[!] Socket error with {peer_id_on_error}: {e}")
                with self.lock:
                    if peer_socket in self.peers: self.peers.remove(peer_socket)
                if peer_socket.fileno() != -1: peer_socket.close()
                break
            except json.JSONDecodeError as e: # pragma: no cover
                decoded_data_snippet = data.decode('utf-8', errors='ignore')[:200]
                print(f"\n[!] Failed to decode JSON from {peer_id}: {e}. Data: '{decoded_data_snippet}'")
            except Exception as e: # pragma: no cover
                print(f"[!] Unexpected error handling message from {peer_id}: {e}")
                break

    def send_message_to_peer(self, peer_socket, message_str_json):
        try:
            peer_socket.sendall(message_str_json.encode('utf-8'))
        except socket.error as e: # pragma: no cover
            peer_id = self._get_peer_id(peer_socket)
            print(f"[!] Error sending message to {peer_id}: {e}")
            with self.lock:
                if peer_socket in self.peers: self.peers.remove(peer_socket)
            if peer_socket.fileno() != -1: peer_socket.close()

    def broadcast_message(self, message_str_json):
        with self.lock:
            for peer_socket in list(self.peers):
                self.send_message_to_peer(peer_socket, message_str_json)

    def _announce_available_tasks(self):
        from message_formats import create_announce_task_message
        with self.task_pool_lock:
            available_tasks_count = sum(1 for task_info in self.offered_tasks.values() if task_info['status'] == 'available')

        if available_tasks_count > 0:
            announce_msg_str = create_announce_task_message(node_id=self.node_id, task_count=available_tasks_count)
            print(f"[*] Node {self.node_id} anunciando {available_tasks_count} tarefa(s) disponível(is)...")
            self.broadcast_message(announce_msg_str)

    def add_task_to_pool(self, operation: str, data: list, task_id:str = None) -> str:
        if not task_id: # pragma: no cover - task_id é geralmente fornecido ou gerado internamente
            task_id = uuid.uuid4().hex

        task_details = {
            'operation': operation, 'data': data,
            'status': 'available', 'assigned_to': None, 'result': None
        }
        with self.task_pool_lock:
            self.offered_tasks[task_id] = task_details
            print(f"[*] Task {task_id} (Op: {operation}, Data: {data}) added to offered tasks pool by {self.node_id}.")

        self._announce_available_tasks()
        return task_id

if __name__ == '__main__':
    from message_formats import (create_task_message, create_result_message, parse_message,
                                 create_announce_task_message, create_request_task_message,
                                 create_no_task_available_message)

    parser = argparse.ArgumentParser(description="P2P Node with Task Pool")
    parser.add_argument('port', type=int, help="Port for the node to listen on")
    parser.add_argument('--host', type=str, default='0.0.0.0', help="Host for the node to listen on (default: 0.0.0.0)")
    parser.add_argument('--peers', type=str, help="Comma-separated list of initial peers to connect to (e.g., 127.0.0.1:8001,127.0.0.1:8002)")

    args = parser.parse_args()
    initial_peer_list = []
    if args.peers:
        peers_str = args.peers.split(',')
        for peer_addr in peers_str:
            try:
                host_val, port_str = peer_addr.split(':')
                initial_peer_list.append((host_val, int(port_str)))
            except ValueError: # pragma: no cover
                print(f"[!] Invalid peer format: {peer_addr}. Skipping.")

    node = P2PNode(args.host, args.port, initial_peer_list)
    node.start_listening()

    print("\n--- P2P Task Pool Node ---")
    print(f"Node ID: {node.node_id}")
    print("Available commands:")
    print("  add <op> <data...>  - Add a task to the pool (e.g., add sum 10 20 5)")
    print("  status              - Show offered and processing tasks")
    print("  text <message...>   - Send a generic text message to peers")
    print("  quit                - Shutdown the node")
    print("--------------------------")

    try:
        while True:
            raw_input_message = input(f"{node.node_id}> ")
            if not raw_input_message: continue # pragma: no cover

            parts = raw_input_message.split()
            command = parts[0].lower()

            if command == 'quit':
                break

            elif command == "add" and len(parts) >= 3:
                op_name = parts[1].lower()
                data_args_str = parts[2:]
                if not data_args_str: # pragma: no cover
                    print(f"[!] 'add {op_name}' requires at least one data argument.")
                    continue
                try:
                    # Para 'sum', converte para float. Outras operações podem manter strings ou ter sua própria conversão.
                    if op_name == "sum":
                        data_args = [float(p) for p in data_args_str]
                    else: # Mantém como string para outras operações, podem ser processadas de forma diferente
                        data_args = data_args_str
                    node.add_task_to_pool(operation=op_name, data=data_args)
                except ValueError: # pragma: no cover
                    print(f"[!] Invalid data for 'add sum' command. All data arguments must be numbers. Got: {data_args_str}")

            elif command == "status":
                with node.task_pool_lock:
                    print("\n--- Offered Tasks (by this node) ---")
                    if node.offered_tasks:
                        for tid, tinfo in node.offered_tasks.items():
                            print(f"  ID: {tid}, Op: {tinfo['operation']}, Data: {tinfo['data']}, "
                                  f"Status: {tinfo['status']}, Assigned: {tinfo.get('assigned_to')}, "
                                  f"Result: {tinfo.get('result')}")
                    else:
                        print("  No tasks currently offered.")
                    print("\n--- Processing Tasks (by this node for others) ---")
                    if node.processing_tasks:
                        for tid, tinfo in node.processing_tasks.items():
                             print(f"  ID: {tid}, Op: {tinfo['operation']}, Data: {tinfo['data']}, "
                                   f"Status: {tinfo['status']}, From: {tinfo.get('requested_from')}")
                    else:
                        print("  No tasks currently being processed for other nodes.")
                    print("--------------------------------------\n")

            elif command == "text" and len(parts) > 1:
                text_content = " ".join(parts[1:])
                # Usar message_formats para criar a mensagem generic_text
                from message_formats import create_generic_text_message # Importação local
                generic_msg_str = create_generic_text_message(content=text_content, sender_id=node.node_id)
                node.broadcast_message(generic_msg_str)
                print(f"[*] Broadcasted TEXT: {text_content}")

            else: # pragma: no cover
                print(f"[!] Unknown command or invalid format: '{raw_input_message}'. Type 'help' for commands (not implemented yet).")
                # Se desejar que texto solto seja enviado como generic_text:
                # from message_formats import create_generic_text_message
                # generic_msg_str = create_generic_text_message(content=raw_input_message, sender_id=node.node_id)
                # node.broadcast_message(generic_msg_str)
                # print(f"[*] Broadcasted raw input as TEXT: {raw_input_message}")


    except KeyboardInterrupt: # pragma: no cover
        print("\n[*] User initiated shutdown (KeyboardInterrupt)...")
    finally:
        print("\n[*] Shutting down node...")
        print("[*] Closing server socket...")
        if node.server_socket:
            try: node.server_socket.close()
            except socket.error as e: print(f"[!] Error closing server socket: {e}") # pragma: no cover

        print("[*] Closing peer connections...")
        with node.lock:
            for peer_sock in node.peers:
                try:
                    if peer_sock.fileno() != -1:
                        peer_sock.shutdown(socket.SHUT_RDWR)
                        peer_sock.close()
                except socket.error as e: # pragma: no cover
                    if peer_sock.fileno() != -1:
                        print(f"[!] Error closing peer socket (FD: {peer_sock.fileno()}): {e}")
                    else:
                        print(f"[!] Error closing an already closed/invalid peer socket: {e}")
        print("[*] Node shut down complete.")
