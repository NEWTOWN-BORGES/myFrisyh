import json
import uuid

# Documentação dos Formatos de Mensagem JSON
# As mensagens são trocadas como strings JSON.

# Tipos de Mensagem Fundamentais:
# 1. TASK: Solicita a execução de uma computação.
#    Exemplo:
#    {
#        "type": "task",
#        "task_id": "unique_task_id",
#        "operation": "sum",
#        "data": [5, 3],
#        "assigned_to": "worker_host:port"  // Opcional, para clareza no contexto de pool
#    }

# 2. RESULT: Envia o resultado de uma tarefa de volta ao solicitante.
#    Exemplo:
#    {
#        "type": "result",
#        "task_id": "original_task_id",
#        "value": 8, // ou null se houver erro
#        "error": null // ou mensagem de erro
#    }

# Tipos de Mensagem para o Sistema de Pool de Tarefas:

# 3. ANNOUNCE_TASK: Um nó (requisitante) anuncia que tem tarefas disponíveis.
#    Exemplo:
#    {
#        "type": "announce_task",
#        "node_id": "requester_host:port",
#        "task_count": 1
#    }

# 4. REQUEST_TASK: Um nó (worker) solicita uma tarefa de um nó anunciante.
#    Exemplo:
#    {
#        "type": "request_task",
#        "worker_id": "worker_host:port"
#    }

# 5. NO_TASK_AVAILABLE: Resposta de um nó anunciante quando não há tarefas.
#    Exemplo:
#    {
#        "type": "no_task_available",
#        "requester_node_id": "requester_host:port"
#    }

# 6. GENERIC_TEXT: Para mensagens de chat simples.
#    Exemplo:
#    {
#        "type": "generic_text",
#        "sender": "node_id_remetente", // Adicionado para identificar o remetente
#        "content": "Olá de Nó2!"
#    }


def create_task_message(operation: str, data: list, task_id: str = None, assigned_to: str = None) -> str:
    """Cria uma mensagem de tarefa (ou ASSIGN_TASK) formatada como JSON."""
    if task_id is None:
        task_id = uuid.uuid4().hex
    message = {
        "type": "task",
        "task_id": task_id,
        "operation": operation,
        "data": data
    }
    if assigned_to:
        message["assigned_to"] = assigned_to
    return json.dumps(message)

def create_result_message(task_id: str, value: any, error: str = None) -> str:
    """Cria uma mensagem de resultado formatada como JSON."""
    message = {
        "type": "result",
        "task_id": task_id,
        "value": value,
        "error": error
    }
    return json.dumps(message)

def create_announce_task_message(node_id: str, task_count: int = 1) -> str:
    """Cria uma mensagem ANNOUNCE_TASK formatada como JSON."""
    message = {
        "type": "announce_task",
        "node_id": node_id,
        "task_count": task_count
    }
    return json.dumps(message)

def create_request_task_message(worker_id: str) -> str:
    """Cria uma mensagem REQUEST_TASK formatada como JSON."""
    message = {
        "type": "request_task",
        "worker_id": worker_id
    }
    return json.dumps(message)

def create_no_task_available_message(requester_node_id: str) -> str:
    """Cria uma mensagem NO_TASK_AVAILABLE formatada como JSON."""
    message = {
        "type": "no_task_available",
        "requester_node_id": requester_node_id
    }
    return json.dumps(message)

def create_generic_text_message(content: str, sender_id: str) -> str:
    """
    Cria uma mensagem de texto genérico formatada como JSON.

    Args:
        content: O conteúdo da mensagem de texto.
        sender_id: O ID do nó que está enviando a mensagem.

    Returns:
        Uma string JSON representando a mensagem de texto genérico.
    """
    message = {
        "type": "generic_text",
        "sender": sender_id,
        "content": content
    }
    return json.dumps(message)

def parse_message(message_json: str) -> dict | None:
    """Analisa uma string JSON em um dicionário Python."""
    try:
        return json.loads(message_json)
    except json.JSONDecodeError:
        return None

if __name__ == '__main__':
    print("--- Exemplos de Mensagens Fundamentais ---")
    task_id_original = uuid.uuid4().hex
    task_msg_str = create_task_message(operation="sum", data=[10, 20], task_id=task_id_original, assigned_to="worker1:8001")
    print("Tarefa (ASSIGN_TASK):", task_msg_str)
    print("Analisado:", parse_message(task_msg_str))

    result_msg_success_str = create_result_message(task_id=task_id_original, value=30)
    print("\nResultado (Sucesso):", result_msg_success_str)
    print("Analisado:", parse_message(result_msg_success_str))

    result_msg_error_str = create_result_message(task_id=task_id_original, value=None, error="Divisão por zero")
    print("\nResultado (Erro):", result_msg_error_str)
    print("Analisado:", parse_message(result_msg_error_str))

    print("\n\n--- Exemplos de Mensagens do Pool de Tarefas ---")
    announce_msg_str = create_announce_task_message(node_id="node_main:8000", task_count=5)
    print("ANNOUNCE_TASK:", announce_msg_str)
    print("Analisado:", parse_message(announce_msg_str))

    request_msg_str = create_request_task_message(worker_id="worker_alpha:8005")
    print("\nREQUEST_TASK:", request_msg_str)
    print("Analisado:", parse_message(request_msg_str))

    no_task_msg_str = create_no_task_available_message(requester_node_id="node_main:8000")
    print("\nNO_TASK_AVAILABLE:", no_task_msg_str)
    print("Analisado:", parse_message(no_task_msg_str))

    print("\n\n--- Exemplo de Mensagem de Texto Genérico ---")
    generic_text_msg_str = create_generic_text_message(content="Olá a todos da rede!", sender_id="node_chatty:7000")
    print("GENERIC_TEXT:", generic_text_msg_str)
    print("Analisado:", parse_message(generic_text_msg_str))


    print("\n\n--- Exemplo de Mensagem Inválida ---")
    invalid_json_str = "{'type': 'task', 'task_id': '123', 'data': [1,2}"
    parsed_invalid_msg = parse_message(invalid_json_str)
    print(f"JSON Inválido ('{invalid_json_str}') -> Analisado: {parsed_invalid_msg}")

    invalid_json_str_2 = '{"type": "task", "task_id": "123", "data": [1,2]'
    parsed_invalid_msg_2 = parse_message(invalid_json_str_2)
    print(f"JSON Malformado ('{invalid_json_str_2}') -> Analisado: {parsed_invalid_msg_2}")
