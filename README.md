README.md
# PoC Blockchain P2P com Docker

Este repositório contém uma prova de conceito de uma rede blockchain minimalista, executada em múltiplos nós Docker, com comunicação P2P e consenso básico.

## Estrutura do Projeto

```
poc-blockchain/
├── node/
│   ├── app.py
│   ├── requirements.txt
│   └── Dockerfile
├── docker-compose.yml
└── test.sh
```

- **node/app.py**: implementação Python + Flask de uma blockchain simples.
- **node/requirements.txt**: dependências (Flask==2.0.3, Werkzeug<2.1.0, requests==2.28.1).
- **node/Dockerfile**: imagem Docker baseada em `python:3.9-slim`.
- **docker-compose.yml**: define 3 serviços (`node1`, `node2`, `node3`) na rede Docker `blockchain-net`.
- **test.sh**: script Bash que registra nós, minera blocos, força consenso e demonstra cadeia inválida.

## Pré-requisitos

- Docker & Docker Compose
- Bash (Linux/macOS)
- Portas 5001, 5002 e 5003 livres no host

## Setup e Execução

1. Clone o repositório e acesse o diretório:
   ```bash
   git clone https://seu-repo-url/poc-blockchain.git
   cd poc-blockchain
   ```
2. Verifique as versões em `node/requirements.txt`:
   ```
   Flask==2.0.3
   Werkzeug<2.1.0
   requests==2.28.1
   ```
3. Construa e suba os containers:
   ```bash
   docker-compose up -d --build
   ```
4. Confira os logs para garantir que os nós iniciaram sem erros:
   ```bash
   docker-compose logs -f
   ```

## Uso e Testes

1. Torne o script de testes executável:
   ```bash
   chmod +x test.sh
   ```
2. Execute o fluxo completo:
   ```bash
   ./test.sh
   ```
3. O `test.sh` irá, em sequência:
   - Registrar nós em `node1`
   - Minerar um bloco em `node1`
   - Exibir a cadeia em `node2`
   - Forçar consenso em `node3`
   - Demonstrar cadeia inválida ao adulterar um bloco em memória

## Demonstração de Bloco Inválido

O passo final do `test.sh` realiza os seguintes passos interna:

1. Busca a cadeia atual via HTTP do próprio nó (`localhost:5000`).
2. Altera o valor da primeira transação do bloco de índice 2.
3. Executa o método `valid_chain` em memória.
4. Deve retornar:
   ```json
   {"valid_chain": false}
   ```
