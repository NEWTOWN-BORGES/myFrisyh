# Protótipo de Nó P2P para Computação Distribuída

Este projeto é um protótipo inicial de um nó peer-to-peer (P2P) em Python, desenvolvido como o primeiro passo para construir uma rede descentralizada para computação de IA e outras tarefas intensivas.

## Funcionalidades Atuais

*   **Comunicação P2P:** Nós podem se conectar uns aos outros.
*   **Troca de Mensagens:** Suporte para mensagens de texto genéricas e mensagens estruturadas (JSON) para tarefas e resultados.
*   **Processamento de Tarefas Simples:** Implementada uma tarefa de exemplo ("sum") onde um nó pode solicitar a outros que somem dois números.
*   **Formato de Mensagem Definido:** Utiliza `message_formats.py` para criar e validar mensagens de tarefa e resultado.

## Arquivos do Projeto

*   `p2p_node.py`: O script principal para rodar um nó P2P.
*   `message_formats.py`: Define os formatos de mensagem JSON para tarefas e resultados e fornece funções auxiliares.
*   `README.md`: Este arquivo.

## Como Executar

1.  **Pré-requisitos:** Python 3.x
2.  **Clonar o repositório (se aplicável) ou ter os arquivos `p2p_node.py` e `message_formats.py` no mesmo diretório.**
3.  **Abrir terminais separados para cada nó que você deseja executar.**

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
    python p2p_node.py <porta_novo_no> --peers <ip_peer1>:<porta_peer1> <ip_peer2>:<porta_peer2> ...
    # Exemplo:
    python p2p_node.py 8002 --peers 127.0.0.1:8000 127.0.0.1:8001
    ```

## Interagindo com os Nós

Uma vez que os nós estão conectados, você pode digitar comandos no terminal de qualquer nó:

*   **Enviar uma tarefa de soma:**
    `task sum <numero1> <numero2>`
    Exemplo: `task sum 10 25`
    O nó que recebe este comando irá transmitir a tarefa para seus peers. Os peers que recebem a tarefa irão processá-la e enviar o resultado de volta ao nó que a originou (o nó que recebeu o comando `task sum...` do usuário).

*   **Enviar uma mensagem de texto genérica:**
    `text <sua_mensagem>`
    Exemplo: `text Olá a todos!`
    A mensagem será transmitida para todos os peers conectados.

*   Qualquer outra entrada de texto (sem `task` ou `text` como prefixo) também será enviada como uma mensagem de texto genérica.

## Formatos de Mensagem (`message_formats.py`)

As mensagens trocadas entre os nós são strings JSON.

*   **Tarefa:**
    ```json
    {
        "type": "task",
        "task_id": "unique_task_identifier_string",
        "operation": "sum", // ou outro tipo de operação
        "data": [5, 3]      // dados para a operação
    }
    ```

*   **Resultado:**
    ```json
    {
        "type": "result",
        "task_id": "original_task_identifier_string",
        "value": 8,     // resultado da computação
        "error": null   // ou uma mensagem de erro string
    }
    ```

*   **Texto Genérico:**
    ```json
    {
        "type": "generic_text",
        "content": "Olá de Nó2!"
    }
    ```

## Próximos Passos (Ideias para Evolução)

Este protótipo é apenas o começo. Aqui estão algumas direções para desenvolvimento futuro:

*   **Mais Tipos de Tarefas:** Implementar operações mais complexas (ex: multiplicação, ou tarefas que simulem pequenos passos de um cálculo de IA ou renderização).
*   **Descoberta de Peers Aprimorada:**
    *   Implementar um mecanismo de broadcast na rede local para descoberta automática.
    *   Considerar um "tracker" centralizado (para bootstrapping) ou uma DHT (Distributed Hash Table) para uma descoberta mais robusta e descentralizada.
*   **Pool de Tarefas:** Nós que têm tarefas poderiam anunciá-las, e nós ociosos poderiam pegá-las de um "pool".
*   **Segurança e Validação:**
    *   Verificação da integridade dos resultados (ex: checksums, ou múltiplos nós executando a mesma subtarefa).
    *   Eventualmente, explorar ZKPs para validação sem revelar dados.
*   **Sistema de Recompensas (Conceitual):**
    *   Como os nós seriam recompensados por contribuir com processamento? (Simulação inicial, antes da blockchain).
*   **Robustez e Tratamento de Erros:** Melhorar a resiliência a falhas de nós e desconexões.
*   **Interface de Usuário:** Uma GUI ou interface web simples para interagir com a rede.
*   **Aprendizado Federado:** Como adaptar a arquitetura para suportar o treinamento de modelos sem que os dados saiam dos dispositivos dos usuários.
*   **Integração Blockchain:** Planejar como as contribuições e recompensas seriam registradas em uma blockchain e como os tokens seriam distribuídos.

---
Este protótipo foi desenvolvido com o auxílio de uma IA de engenharia de software.
```
