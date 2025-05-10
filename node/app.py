#!/usr/bin/env python3

import os
import hashlib
import json
from time import time
from uuid import uuid4
from urllib.parse import urlparse

import requests
from flask import Flask, jsonify, request


class Blockchain:
    def __init__(self):
        self.current_transactions = []
        self.chain = []
        self.nodes = set()

        # Cria o bloco gênese
        self.new_block(previous_hash='1', proof=100)

    def register_node(self, address):
        """
        Adiciona um novo nó à lista de nós da rede.
        :param address: URL do nó (e.g. 'http://node2:5000')
        """
        parsed = urlparse(address)
        if parsed.netloc:
            self.nodes.add(f"{parsed.scheme}://{parsed.netloc}")
        elif parsed.path:
            # Caso a URL seja sem esquema
            self.nodes.add(parsed.path)
        else:
            raise ValueError('URL de nó inválida')

    def valid_chain(self, chain):
        """
        Verifica se a blockchain fornecida é válida.
        :param chain: lista de blocos
        :return: True se válida, False caso contrário
        """
        last_block = chain[0]
        current_index = 1

        while current_index < len(chain):
            block = chain[current_index]
            # Verifica hash do bloco anterior
            if block['previous_hash'] != self.hash(last_block):
                return False
            # Verifica proof‐of‐work
            if not self.valid_proof(last_block['proof'], block['proof']):
                return False

            last_block = block
            current_index += 1

        return True

    def resolve_conflicts(self):
        """
        Algoritmo de consenso:
        Substitui a cadeia local pela mais longa entre os nós.
        :return: True se foi substituída, False caso contrário
        """
        neighbours = self.nodes
        new_chain = None

        max_length = len(self.chain)

        for node in neighbours:
            try:
                resp = requests.get(f"{node}/chain")
                if resp.status_code == 200:
                    length = resp.json()['length']
                    chain = resp.json()['chain']
                    if length > max_length and self.valid_chain(chain):
                        max_length = length
                        new_chain = chain
            except requests.exceptions.RequestException:
                # Nó indisponível; ignora
                continue

        if new_chain:
            self.chain = new_chain
            return True

        return False

    def new_block(self, proof, previous_hash=None):
        """
        Cria um novo bloco na cadeia.
        :param proof: proof fornecido pelo PoW
        :param previous_hash: hash do bloco anterior
        :return: novo bloco
        """
        block = {
            'index': len(self.chain) + 1,
            'timestamp': time(),
            'transactions': self.current_transactions,
            'proof': proof,
            'previous_hash': previous_hash or self.hash(self.chain[-1]),
        }

        # Reinicia lista de transações
        self.current_transactions = []
        self.chain.append(block)
        return block

    def new_transaction(self, sender, recipient, amount):
        """
        Cria uma nova transação para o próximo bloco a ser minerado.
        :param sender: endereço do remetente
        :param recipient: endereço do destinatário
        :param amount: valor
        :return: índice do bloco que irá receber esta transação
        """
        self.current_transactions.append({
            'sender': sender,
            'recipient': recipient,
            'amount': amount,
        })
        return self.last_block['index'] + 1

    @staticmethod
    def hash(block):
        """
        Retorna o hash SHA-256 de um bloco.
        :param block: bloco
        """
        # Garante ordem consistente das chaves
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    @property
    def last_block(self):
        return self.chain[-1]

    def proof_of_work(self, last_proof):
        """
        Algoritmo simples de PoW:
        - Encontre um número p tal que hash(pp') comece com 4 zeros,
          onde p é proof anterior e p' é o novo proof
        """
        proof = 0
        while not self.valid_proof(last_proof, proof):
            proof += 1
        return proof

    @staticmethod
    def valid_proof(last_proof, proof):
        """
        Valida o proof: hash(last_proof, proof) começa com 4 zeros?
        """
        guess = f"{last_proof}{proof}".encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:4] == "0000"


# Inicializa o Flask e o blockchain
app = Flask(__name__)
node_identifier = str(uuid4()).replace('-', '')
blockchain = Blockchain()

# Registra nós vizinhos passados pela variável de ambiente PEERS
peers_env = os.getenv('PEERS')
if peers_env:
    for peer in peers_env.split(','):
        blockchain.register_node(peer.strip())


@app.route('/mine', methods=['GET'])
def mine():
    # Realiza PoW
    last_block = blockchain.last_block
    proof = blockchain.proof_of_work(last_block['proof'])

    # Recompensa pela mineração
    blockchain.new_transaction(
        sender="0",
        recipient=node_identifier,
        amount=1,
    )

    # Cria novo bloco e adiciona à cadeia
    previous_hash = blockchain.hash(last_block)
    block = blockchain.new_block(proof, previous_hash)

    response = {
        'message': "Novo bloco forjado",
        'index': block['index'],
        'transactions': block['transactions'],
        'proof': block['proof'],
        'previous_hash': block['previous_hash'],
    }
    return jsonify(response), 200


@app.route('/transactions/new', methods=['POST'])
def new_transaction():
    values = request.get_json()
    # Valida payload
    required = ['sender', 'recipient', 'amount']
    if not all(k in values for k in required):
        return jsonify({'message': 'Dados de transação incompletos'}), 400

    index = blockchain.new_transaction(
        values['sender'],
        values['recipient'],
        values['amount']
    )
    return jsonify({'message': f'Transação será adicionada ao bloco {index}'}), 201


@app.route('/chain', methods=['GET'])
def full_chain():
    response = {
        'chain': blockchain.chain,
        'length': len(blockchain.chain),
    }
    return jsonify(response), 200


@app.route('/nodes/register', methods=['POST'])
def register_nodes():
    values = request.get_json()
    nodes = values.get('nodes')
    if not nodes:
        return jsonify({'message': 'Envie uma lista de nós válida'}), 400

    for node in nodes:
        blockchain.register_node(node)

    return jsonify({
        'message': 'Nós registrados com sucesso',
        'total_nodes': list(blockchain.nodes)
    }), 201


@app.route('/nodes/resolve', methods=['GET'])
def consensus():
    replaced = blockchain.resolve_conflicts()
    if replaced:
        return jsonify({
            'message': 'Nossa cadeia foi substituída',
            'new_chain': blockchain.chain
        }), 200
    else:
        return jsonify({
            'message': 'Nossa cadeia é autoritária',
            'chain': blockchain.chain
        }), 200


if __name__ == '__main__':
    # Rodar na porta 5000 por padrão
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port)