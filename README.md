# Protótipo de Nó P2P para Computação Distribuída

Este projeto é um protótipo inicial de um nó peer-to-peer (P2P) em Python, desenvolvido como parte da construção de uma rede descentralizada para computação de IA e outras tarefas intensivas.

## Funcionalidades Atuais

*   **Comunicação P2P:** Nós podem se conectar uns aos outros e trocar mensagens.
*   **Sistema de Pool de Tarefas:**
    *   Nós podem adicionar tarefas (ex: "sum") ao seu pool local de tarefas ofertadas.
    *   As tarefas disponíveis são anunciadas na rede.
    *   Nós ociosos (trabalhadores) podem solicitar tarefas dos nós anunciantes.
    *   As tarefas são atribuídas aos trabalhadores, processadas, e os resultados são enviados de volta ao nó requisitante original.
*   **Troca de Mensagens Estruturadas:** Utiliza JSON para todos os tipos de comunicação, incluindo tarefas, resultados, anúncios e mensagens de texto genéricas. Definido em `message_formats.py`.
*   **Interface de Linha de Comando (CLI):** Para interagir com o nó, adicionar tarefas, verificar status e enviar mensagens de texto.

## Arquivos do Projeto

*   `p2p_node.py`: O script principal para rodar um nó P2P com funcionalidades de pool de tarefas.
*   `message_formats.py`: Define os formatos de mensagem JSON e fornece funções auxiliares para criar e analisar mensagens.
*   `README.md`: Este arquivo.

## Como Funciona o Sistema de Pool de Tarefas

1.  **Adição e Anúncio:**
    *   Um usuário, através da CLI de um nó (vamos chamá-lo de Nó Requisitante), usa o comando `add <operação> <dados...>` (ex: `add sum 10 20`).
    *   A tarefa é adicionada ao pool de "tarefas ofertadas" (`offered_tasks`) do Nó Requisitante com um status "available".
    *   O Nó Requisitante então transmite uma mensagem `ANNOUNCE_TASK` para todos os seus peers, informando que tem tarefas disponíveis e quantas são.

2.  **Solicitação de Tarefa:**
    *   Outros nós na rede (vamos chamá-los de Nós Trabalhadores) recebem a mensagem `ANNOUNCE_TASK`.
    *   Se um Nó Trabalhador estiver ocioso (não estiver processando outra tarefa no momento), ele envia uma mensagem `REQUEST_TASK` de volta ao Nó Requisitante que fez o anúncio. Esta mensagem inclui o `worker_id` do Nó Trabalhador.

3.  **Atribuição da Tarefa:**
    *   O Nó Requisitante recebe a `REQUEST_TASK`.
    *   Ele procura uma tarefa com status "available" em seu `offered_tasks`.
        *   **Se uma tarefa estiver disponível:** O Nó Requisitante marca a tarefa como "pending", registra o `worker_id` do solicitante no campo `assigned_to` da tarefa, e envia a tarefa completa (usando o formato de mensagem `task`, que aqui atua como `ASSIGN_TASK`) diretamente ao Nó Trabalhador que a solicitou.
        *   **Se nenhuma tarefa estiver disponível** (ex: outra já foi atribuída): O Nó Requisitante envia uma mensagem `NO_TASK_AVAILABLE` para o Nó Trabalhador.

4.  **Processamento e Resultado:**
    *   O Nó Trabalhador recebe a mensagem `task` (ASSIGN_TASK). Ele armazena os detalhes da tarefa em seu pool `processing_tasks` e começa a executá-la.
    *   Após o processamento, o Nó Trabalhador cria uma mensagem `result` contendo o `task_id` original e o valor calculado (ou um erro, se ocorrer).
    *   Esta mensagem `result` é enviada de volta ao Nó Requisitante (o nó de quem recebeu a tarefa).
    *   O Nó Trabalhador então remove a tarefa de seu `processing_tasks` (ou marca como concluída).

5.  **Conclusão da Tarefa:**
    *   O Nó Requisitante recebe a mensagem `result`.
    *   Ele encontra a tarefa correspondente em seu `offered_tasks` (que deveria estar com status "pending" e atribuída ao trabalhador que enviou o resultado).
    *   O status da tarefa é atualizado para "completed", e o resultado é armazenado.

## Como Executar

1.  **Pré-requisitos:** Python 3.x
2.  **Arquivos:** Certifique-se de que `p2p_node.py` e `message_formats.py` estejam no mesmo diretório.
3.  **Abrir terminais separados para cada nó.**

4.  **Iniciar o primeiro nó (Nó A):**
    ```bash
    python p2p_node.py <porta_no_A>
    # Exemplo:
    python p2p_node.py 8000
    ```

5.  **Iniciar um segundo nó (Nó B) e conectá-lo ao Nó A:**
    ```bash
    python p2p_node.py <porta_no_B> --peers <ip_no_A>:<porta_no_A>
    # Exemplo (se o Nó A está em 127.0.0.1:8000):
    python p2p_node.py 8001 --peers 127.0.0.1:8000
    ```

6.  **Iniciar mais nós, conectando-os a peers existentes:**
    ```bash
    python p2p_node.py <porta_novo_no> --peers <ip_peer1>:<porta_peer1> [<ip_peer2>:<porta_peer2> ...]
    # Exemplo:
    python p2p_node.py 8002 --peers 127.0.0.1:8000 127.0.0.1:8001
    ```

## Interagindo com os Nós (CLI)

Uma vez que os nós estão conectados, você pode digitar comandos no terminal de qualquer nó:

*   **Adicionar uma tarefa ao pool do nó atual:**
    `add <operação> <dado1> [<dado2> ...]`
    Exemplo para somar números: `add sum 10 20 5`
    Exemplo para outra operação (os dados serão passados como strings): `add process_image image_01.png --brightness 0.5`
    O nó adicionará esta tarefa ao seu pool de "tarefas ofertadas" e anunciará automaticamente a disponibilidade aos seus peers.

*   **Verificar o status das tarefas do nó atual:**
    `status`
    Este comando exibe as tarefas no pool de "tarefas ofertadas" (`offered_tasks`) e as tarefas que o nó está processando atualmente para outros (`processing_tasks`), incluindo seus status, quem as atribuiu, etc.

*   **Enviar uma mensagem de texto genérica para todos os peers:**
    `text <sua_mensagem>`
    Exemplo: `text Olá a todos da rede!`

*   **Sair do nó:**
    `quit`

## Formatos de Mensagem (`message_formats.py`)

As mensagens trocadas entre os nós são strings JSON. Abaixo estão os principais tipos:

*   **`task` (usada também como `ASSIGN_TASK`):**
    ```json
    {
        "type": "task",
        "task_id": "unique_task_identifier_string",
        "operation": "sum",
        "data": [10, 20, 5],
        "assigned_to": "worker_id_string" // Opcional, presente quando atribuindo a um worker específico
    }
    ```

*   **`result`:**
    ```json
    {
        "type": "result",
        "task_id": "original_task_identifier_string",
        "value": 35,     // resultado da computação (pode ser null se houver erro)
        "error": null   // ou uma mensagem de erro string
    }
    ```

*   **`ANNOUNCE_TASK`:**
    ```json
    {
        "type": "announce_task",
        "node_id": "node_id_do_anunciante", // ex: "127.0.0.1:8000"
        "task_count": 3 // número de tarefas disponíveis
    }
    ```

*   **`REQUEST_TASK`:**
    ```json
    {
        "type": "request_task",
        "worker_id": "node_id_do_trabalhador" // ex: "127.0.0.1:8001"
    }
    ```

*   **`NO_TASK_AVAILABLE`:**
    ```json
    {
        "type": "no_task_available",
        "requester_node_id": "node_id_do_anunciante_que_nao_tem_tarefas"
    }
    ```

*   **`generic_text`:**
    ```json
    {
        "type": "generic_text",
        "sender": "node_id_do_remetente", // ex: "127.0.0.1:8002"
        "content": "Olá a todos!"
    }
    ```

## Próximos Passos (Ideias para Evolução)

Este protótipo é apenas o começo. Aqui estão algumas direções para desenvolvimento futuro:

*   **Mais Tipos de Tarefas:** Implementar operações mais complexas e variadas.
*   **Descoberta de Peers Aprimorada:**
    *   Mecanismos de broadcast na rede local para descoberta automática.
    *   Considerar um "tracker" ou DHT para descoberta em redes maiores.
*   **Gerenciamento de Tarefas Aprimorado:**
    *   Priorização de tarefas.
    *   Tratamento de falhas de workers (timeout, reatribuição de tarefas).
    *   Distribuição de tarefas baseada na carga ou capacidade dos workers.
*   **Segurança e Validação:**
    *   Verificação da integridade dos resultados.
    *   Autenticação de nós.
*   **Sistema de Recompensas (Conceitual):**
    *   Mecanismos (simulados inicialmente) para recompensar nós por contribuírem com processamento.
*   **Robustez e Tratamento de Erros:** Melhorar a resiliência geral da rede.
*   **Interface de Usuário:** Uma GUI ou interface web para facilitar a interação.
*   **Aprendizado Federado:** Adaptar a arquitetura para suportar o treinamento de modelos de IA sem que os dados brutos saiam dos dispositivos dos usuários.
*   **Integração Blockchain:** Planejar como as contribuições e recompensas poderiam ser registradas em uma blockchain.

---
Este protótipo foi desenvolvido com o auxílio de uma IA de engenharia de software.
```
