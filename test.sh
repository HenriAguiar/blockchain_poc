#!/usr/bin/env bash
set -e

# 1) Registrar nós em node1
echo "==> Registrando nós em node1"
curl -s -X POST http://localhost:5001/nodes/register \
     -H "Content-Type: application/json" \
     -d '{"nodes":["http://node2:5000","http://node3:5000"]}'
echo -e "\n"

# 2) Minerar um bloco em node1
echo "==> Minerando um bloco em node1"
curl -s http://localhost:5001/mine
echo -e "\n"

# 3) Verificar a cadeia em node2
echo "==> Cadeia em node2"
curl -s http://localhost:5002/chain
echo -e "\n"

# 4) Forçar consenso em node3
echo "==> Forçando consenso em node3"
curl -s http://localhost:5003/nodes/resolve
echo -e "\n"

# 5) Demonstração de bloco inválido em node1
echo "==> Demonstrando cadeia inválida após adulteração em node1"
docker exec -i poc-blockchain_node1_1 python3 - << 'PYCODE'
import requests, json
from app import Blockchain

# 5.1) Busca a cadeia atual a partir do próprio nó
data = requests.get('http://localhost:5000/chain').json()
chain = data['chain']

# 5.2) Adulteração: muda o valor da primeira transação do bloco de índice 2 (chain[1])
if len(chain) > 1 and chain[1]['transactions']:
    chain[1]['transactions'][0]['amount'] = 4242

# 5.3) Valida a cadeia adulterada
print(json.dumps({
    "valid_chain": Blockchain().valid_chain(chain)
}, ensure_ascii=False))
PYCODE