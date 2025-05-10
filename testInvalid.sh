#!/usr/bin/env bash
set -euo pipefail
# … comandos anteriores …

# 5) Demonstrar bloco inválido
echo -e "\n>>> Demonstrando bloco inválido em node1"
docker exec -i poc-blockchain_node1_1 python3 - << 'PYCODE'
from app import blockchain
chain = blockchain.chain
if len(chain) > 1 and chain[1]['transactions']:
    chain[1]['transactions'][0]['amount'] = 4242
print("Chain válida?", blockchain.valid_chain(chain))
PYCODE