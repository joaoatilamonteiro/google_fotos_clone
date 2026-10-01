import json
import os.path
from collections import Counter

# Carrega o arquivo JSON
base_pasta = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(base_pasta, "embeddings_mestre.json"), 'r', encoding='utf-8') as f:
    dados = json.load(f)

# Substitua 'nome' pela chave exata que guarda a identificação no seu JSON
# (pode ser 'label', 'person', 'identificacao', etc.)
nomes = [item.get('nome', 'Desconhecido') for item in dados]
contagem = Counter(nomes)

print("Aparições por pessoa:")
for nome, qtd in contagem.most_common():
    print(f"{nome}: {qtd}")