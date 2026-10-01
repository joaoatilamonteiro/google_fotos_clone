import json
import cv2
import os

#prototipo!!!
base_pasta = os.path.dirname(os.path.abspath(__file__))
caminho_json = (os.path.join(base_pasta, "embeddings_mestre.json"))

# Carrega o cofre de embeddings
with open(caminho_json, "r", encoding="utf-8") as arquivo:
    banco_rostos = json.load(arquivo)

modificados = 0

print("=== Assistente de Rotulagem de Rostos ===")
print("DICAS:")
print(" - Digite o nome da pessoa.")
print(" - Digite 'pular' (ou dê Enter vazio) se não souber quem é ou for um erro da IA.")
print(" - Digite 'sair' para parar, salvar tudo e fechar.\n")

for rosto in banco_rostos:
    # Se o rosto já tem um nome salvo, pula para o próximo
    if "nome" in rosto:
        continue

    caminho_imagem = rosto["caminho_recorte"]

    # Prevenção: verifica se você não apagou a foto sem querer
    if not os.path.exists(caminho_imagem):
        print(f"⚠️ Imagem não encontrada, pulando: {caminho_imagem}")
        continue

    # Abre a foto com OpenCV
    imagem = cv2.imread(caminho_imagem)

    # Redimensiona o recorte para 300x300 pixels para você conseguir enxergar bem na tela
    imagem_tela = cv2.resize(imagem, (300, 300), interpolation=cv2.INTER_AREA)

    cv2.imshow("Quem e essa pessoa?", imagem_tela)
    cv2.waitKey(1)  # Atualiza a janela do Windows

    # Pede o nome no terminal do seu editor
    nome = input("Nome do rosto na tela: ").strip()

    if nome.lower() == 'sair':
        print("\nInterrompendo rotulagem...")
        break
    elif nome.lower() == 'pular' or nome == '':
        rosto["nome"] = "Desconhecido"
    else:
        rosto["nome"] = nome

    modificados += 1

cv2.destroyAllWindows()

# Salva o arquivo JSON atualizado por cima do antigo
if modificados > 0:
    with open(caminho_json, "w", encoding="utf-8") as arquivo:
        json.dump(banco_rostos, arquivo, ensure_ascii=False, indent=4)
    print(f"\n🎉 Progresso salvo com sucesso! {modificados} rostos ganharam identidade.")
else:
    print("\nNenhuma alteração nova foi feita.")