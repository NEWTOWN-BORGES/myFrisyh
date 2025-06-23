import json
import uuid

# Documentação dos Formatos de Mensagem JSON
# As mensagens são trocadas como strings JSON.

# 1. Formato da Tarefa (Task Message)
# Usado para solicitar a um nó que execute uma computação.
# Exemplo:
# {
#     "type": "task",  # Tipo da mensagem, sempre "task"
#     "task_id": "unique_task_identifier_string",  # Identificador único da tarefa
#     "operation": "sum",  # Operação a ser realizada (ex: "sum", "multiply")
#     "data": [5, 3]  # Dados para a operação (lista de operandos, etc.)
# }

# 2. Formato do Resultado (Result Message)
# Usado para enviar o resultado de uma tarefa de volta ao solicitante.
# Exemplo de sucesso:
# {
#     "type": "result",  # Tipo da mensagem, sempre "result"
#     "task_id": "original_task_identifier_string",  # ID da tarefa original
#     "value": 8,  # O resultado da computação
#     "error": null  # Null se não houver erro
# }
# Exemplo de erro:
# {
#     "type": "result",
#     "task_id": "original_task_identifier_string",
#     "value": null,
#     "error": "Error message string if something went wrong"
# }

def create_task_message(operation: str, data: list, task_id: str = None) -> str:
    """
    Cria uma mensagem de tarefa formatada como uma string JSON.

    Args:
        operation: O tipo de operação a ser realizada (ex: "sum", "multiply").
        data: Os dados necessários para a operação (lista).
        task_id: Um identificador único opcional para a tarefa.
                 Se None, um novo UUID será gerado.

    Returns:
        Uma string JSON representando a mensagem da tarefa.
    """
    if task_id is None:
        task_id = uuid.uuid4().hex

    message = {
        "type": "task",
        "task_id": task_id,
        "operation": operation,
        "data": data
    }
    return json.dumps(message)

def create_result_message(task_id: str, value: any, error: str = None) -> str:
    """
    Cria uma mensagem de resultado formatada como uma string JSON.

    Args:
        task_id: O task_id da tarefa original.
        value: O resultado da computação. Pode ser None se houver um erro.
        error: Uma mensagem de erro se a tarefa falhou, caso contrário None.

    Returns:
        Uma string JSON representando a mensagem de resultado.
    """
    message = {
        "type": "result",
        "task_id": task_id,
        "value": value,
        "error": error
    }
    return json.dumps(message)

def parse_message(message_json: str) -> dict | None:
    """
    Analisa uma string JSON em um dicionário Python.

    Args:
        message_json: A string JSON a ser analisada.

    Returns:
        Um dicionário Python se a análise for bem-sucedida,
        None se a string de entrada não for um JSON válido.
    """
    try:
        return json.loads(message_json)
    except json.JSONDecodeError:
        # Poderia logar o erro aqui se necessário
        # print(f"Erro ao decodificar JSON: {e}")
        return None

if __name__ == '__main__':
    print("--- Exemplo de Mensagem de Tarefa ---")
    # Criar uma mensagem de tarefa de exemplo
    task_msg_str = create_task_message(operation="sum", data=[10, 20])
    print("String JSON da Tarefa:", task_msg_str)

    # Analisar a mensagem de tarefa de volta para um dicionário
    parsed_task_msg = parse_message(task_msg_str)
    if parsed_task_msg:
        print("Dicionário da Tarefa Analisado:", parsed_task_msg)
        task_id_original = parsed_task_msg.get("task_id")
    else:
        print("Falha ao analisar a mensagem de tarefa.")
        task_id_original = "dummy_task_id_for_example"

    print("\n--- Exemplo de Mensagem de Resultado (Sucesso) ---")
    # Criar uma mensagem de resultado de exemplo (sucesso)
    result_msg_success_str = create_result_message(task_id=task_id_original, value=30)
    print("String JSON do Resultado (Sucesso):", result_msg_success_str)

    # Analisar a mensagem de resultado de volta para um dicionário
    parsed_result_success_msg = parse_message(result_msg_success_str)
    if parsed_result_success_msg:
        print("Dicionário do Resultado (Sucesso) Analisado:", parsed_result_success_msg)
    else:
        print("Falha ao analisar a mensagem de resultado (sucesso).")

    print("\n--- Exemplo de Mensagem de Resultado (Erro) ---")
    # Criar uma mensagem de resultado de exemplo (erro)
    result_msg_error_str = create_result_message(task_id=task_id_original, value=None, error="Divisão por zero")
    print("String JSON do Resultado (Erro):", result_msg_error_str)

    # Analisar a mensagem de resultado de volta para um dicionário
    parsed_result_error_msg = parse_message(result_msg_error_str)
    if parsed_result_error_msg:
        print("Dicionário do Resultado (Erro) Analisado:", parsed_result_error_msg)
    else:
        print("Falha ao analisar a mensagem de resultado (erro).")

    print("\n--- Exemplo de Mensagem Inválida ---")
    invalid_json_str = "{'type': 'task', 'task_id': '123', 'data': [1,2}" # JSON inválido
    parsed_invalid_msg = parse_message(invalid_json_str)
    if parsed_invalid_msg is None:
        print("Mensagem inválida corretamente identificada como None.")
    else:
        print("Erro: Mensagem inválida não foi tratada corretamente.")
