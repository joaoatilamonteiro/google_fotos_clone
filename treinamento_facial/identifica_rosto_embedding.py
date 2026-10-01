import os
import cv2
from deepface import DeepFace
import json
import re

def limpa_caminho(caminho):
    return re.sub(r'[\\/:*?"<>|\s]+', "_", caminho).strip(" _")

def caca_foto(pasta):
    caminhos = []
    for raiz, diretorio, arquivos in os.walk(pasta):
        for arquivo in arquivos:
            if arquivo.lower().endswith(".jpg"):
                caminhos.append(os.path.join(raiz, arquivo))
    return caminhos

base_pasta = os.path.dirname(os.path.abspath(__file__))
caminho_fotos_originais = r"AONDE DEVE INSERIR AS FOTOS"
fotos = caca_foto(caminho_fotos_originais)


banco_rostos = []
index_pasta = 0

for foto in fotos:
    caminho_pastas_rosto_completo = None

    print(f"analisando foto: {foto}")
    try:
        resultados = DeepFace.represent(
            img_path=foto,
            model_name="Facenet",
            detector_backend="retinaface"
        )
        imagem_original = cv2.imread(foto)

        if caminho_pastas_rosto_completo is None:
            index_pasta +=1
            caminho_pastas_rosto_completo = os.path.join(base_pasta,"pasta_fotos",limpa_caminho(caminho_fotos_originais), str(index_pasta))
            os.makedirs(caminho_pastas_rosto_completo, exist_ok=True)

        rostos_reais = 0

        for indice, rosto in enumerate(resultados):
            area = rosto["facial_area"]
            x, y, w, h = area["x"], area["y"], area["w"], area["h"]

            confianca = rosto.get("face_confidence", 0)
            # Recorta exatamente o quadrado onde está o rosto
            if confianca < 0.95 or w < 80 or h < 80:
                continue


            # Define o tamanho da margem extra em pixels (ex: 50 pixels para cada lado)
            margem = 50

            # Pega as dimensões máximas da foto original para não cortar fora da imagem
            altura_max, largura_max = imagem_original.shape[:2]

            # Calcula as novas coordenadas expandidas com trava de segurança
            novo_y = max(0, y - margem)
            novo_y_fim = min(altura_max, y + h + margem)

            novo_x = max(0, x - margem)
            novo_x_fim = min(largura_max, x + w + margem)

            # Recorta a imagem usando as novas coordenadas expandidas
            recorte = imagem_original[novo_y:novo_y_fim, novo_x:novo_x_fim]

            cinza = cv2.cvtColor(recorte, cv2.COLOR_BGR2GRAY)
            nitidez = cv2.Laplacian(cinza, cv2.CV_64F).var()

            if nitidez < 50.0:
                continue



            rostos_reais +=1


            # Salva esse recorte como um arquivo visual para você conferir
            nome_arquivo = f"rosto_{rostos_reais}.jpg"
            caminho_arquivo = os.path.join(caminho_pastas_rosto_completo, nome_arquivo)
            cv2.imwrite(caminho_arquivo, recorte)
            vetor = rosto["embedding"]

            banco_rostos.append({
                "foto_original": foto,
                "caminho_recorte": caminho_arquivo,
                "embedding": vetor
            })
            print(f"✅ Rosto {rostos_reais} salvo (Confiança: {confianca:.2f}) -> {nome_arquivo}")

        if rostos_reais == 0:
            print("nenhum rosto superou os filtros de segurança")

    except ValueError:
        print("nenhum rosto encontrado, pulando para proxima foto")
caminho_json_unico = os.path.join(os.path.dirname(os.path.abspath(__file__)),"embeddings_mestre.json")

with open(caminho_json_unico, "w", encoding="utf-8") as arquivo_json:
    json.dump(banco_rostos, arquivo_json, ensure_ascii=False, indent=4)

print(f"\n🎉 Extração concluída! {len(banco_rostos)} rostos válidos salvos no JSON: {caminho_json_unico}")
