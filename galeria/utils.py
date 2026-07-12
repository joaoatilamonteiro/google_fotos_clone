import hashlib
from PIL import Image, ImageOps
from PIL.ExifTags import TAGS
from datetime import datetime
import os

def gerar_hash(caminho_arquivo):
    #gera identifacador para nao ter fotos repetidas, ele le a imagem byte por byte e gera um hash unico.
    #parecido com o que acontece no código do spotify

    hash_sha256 = hashlib.sha256()

    try:
        with open(caminho_arquivo, "rb") as arquivo:
            for bloco in iter(lambda: arquivo.read(4096), b""):
                hash_sha256.update(bloco)

        return hash_sha256.hexdigest()

    except Exception as erro:
        print(f"erro ao gerar hash: erro: {erro}")
        return None


def extrai_metadados(caminho_arquivo):

    dados = {"celular": None,
             "data": None}

    try:
        imagem = Image.open(caminho_arquivo)
        exif_bruto = imagem.getexif() #ele pega os codigos exif para descobrir a data e o celular

        if not exif_bruto:
            return dados

        exif = {}
        for tag_id, valor in exif_bruto.items():
            nome_tag = TAGS.get(tag_id, tag_id)
            exif[nome_tag] = valor

        # Resgatando o modelo do celular/câmera
        if 'Model' in exif:
            dados['celular'] = str(exif['Model']).strip()

        # Resgatando a data original e convertendo para o formato de tempo do Python
        if 'DateTimeOriginal' in exif or 'DateTime' in exif:
            data_string = exif.get('DateTimeOriginal', exif.get('DateTime'))
            dados['data'] = datetime.strptime(data_string, '%Y:%m:%d %H:%M:%S')

    except Exception as erro:
        print(f"deu o erro {erro}")
    return dados

def cria_miniatura(caminho_arquivo, caminho_arquivo_dest, tamanho = (400,400)):
    try:
        imagem = Image.open(caminho_arquivo)

        miniatura_quad = ImageOps.fit(imagem, tamanho, Image.Resampling.LANCZOS)

        os.makedirs(os.path.dirname(caminho_arquivo_dest), exist_ok=True)

        miniatura_quad.save(caminho_arquivo_dest, format="JPEG", quality = 75)

        return True



    except Exception as erro:
        print(f"deu um erro ai, erro {erro}")
        return False