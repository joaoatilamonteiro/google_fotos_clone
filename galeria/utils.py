import hashlib
from PIL import Image, ImageOps
from PIL.ExifTags import TAGS, GPSTAGS
from datetime import datetime
import os
import cv2
from pillow_heif import register_heif_opener
from pymediainfo import MediaInfo
from timezonefinder import TimezoneFinder

register_heif_opener()

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


def extrai_metadados_foto(caminho_foto):

    dados = {"celular": None,
             "data": None,
             "largura_pixel": None,
             "altura_pixel": None,
             "orientacao": None,
             "latitude":None,
             "longitude":None,
             "fuso_horario":None}

    try:
        imagem = Image.open(caminho_foto)
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

        if "ImageWidth" in exif:
            dados["largura_pixel"] = int(exif["ImageWidth"])
        if "ImageLength" in exif:
            dados["altura_pixel"] = int(exif["ImageLength"])

        if dados["largura_pixel"] and dados["altura_pixel"]:
            if dados["largura_pixel"] > dados["altura_pixel"]:
                dados["orientacao"] = "Deitado"
            elif dados["altura_pixel"] > dados["largura_pixel"]:
                dados["orientacao"] = "Em pé"
            elif dados["altura_pixel"] == dados["largura_pixel"]:
                dados["orientacao"] = "Foto quadrada"

        gps_ifd = exif_bruto.get_ifd(34853)
        if gps_ifd:
            gps_dados = {}
            for tag_id, valor in gps_ifd.items():
                # Usa o GPSTAGS em vez do TAGS normal
                nome_tag = GPSTAGS.get(tag_id, tag_id)
                gps_dados[nome_tag] = valor
            if "GPSLatitude" in gps_dados and "GPSLongitude" in gps_dados:
                latitude = gps_dados["GPSLatitude"]
                longitude = gps_dados["GPSLongitude"]

                latitude_ref = gps_dados.get('GPSLatitudeRef', 'N')
                longitude_ref = gps_dados.get('GPSLongitudeRef', 'E')

                lat_decimal = float(latitude[0]) + (float(latitude[1]) / 60.0) + (float(latitude[2]) / 3600.0)
                if latitude_ref == 'S':
                    lat_decimal = -lat_decimal

                # Convertendo Longitude (Graus, Minutos, Segundos -> Decimal)
                lon_decimal = float(longitude[0]) + (float(longitude[1]) / 60.0) + (float(longitude[2]) / 3600.0)
                if longitude_ref == 'W':
                    lon_decimal = -lon_decimal

                dados["latitude"] = lat_decimal
                dados["longitude"] = lon_decimal

                tf = TimezoneFinder()
                nome_fuso = tf.timezone_at(lng=lon_decimal, lat=lat_decimal)
                dados["fuso_horario"] = nome_fuso



    except Exception as erro:
        print(f"deu o erro {erro}")
    return dados

def extrai_metadados_video(caminho_video):
    dados = {"caminho_original": None,
             "data":None,
             "celular": None,
             "duracao":None,
             "largura_pixel":None,
             "altura_pixel":None}

    try:
        media_info = MediaInfo.parse(caminho_video)
        for video in media_info.tracks:
            if video.track_type == "General":
                dados["caminho_original"] = getattr(video, "complete_name", None)
                dados["data"] = getattr(video, "encoded_date", None)
                dados["celular"] =getattr(video, "performer", None)
                dados["duracao"] = getattr(video, "duration", None)

            if video.track_type == "Video":
                dados["largura_pixel"] = getattr(video, "width", None)
                dados["altura_pixel"] = getattr(video, "height", None)
    except Exception as e:
        print(f"erro ao processar")
    return dados

def cria_miniatura_foto(caminho_arquivo, caminho_arquivo_dest, tamanho = (400, 400)):
    try:
        imagem = Image.open(caminho_arquivo)

        miniatura_quad = ImageOps.fit(imagem, tamanho, Image.Resampling.LANCZOS)

        os.makedirs(os.path.dirname(caminho_arquivo_dest), exist_ok=True)

        miniatura_quad.save(caminho_arquivo_dest, format="JPEG", quality = 75)

        return True

    except Exception as erro:
        print(f"deu um erro ai, erro {erro}")
        return False

def cria_miniatura_video(caminho_arquivo, caminho_arquivo_dest, tamanho =(400, 400)):
    try:
        video = cv2.VideoCapture(caminho_arquivo)
        sucesso,frame = video.read()

        if sucesso:
            frame_dimensionado = cv2.resize(frame,tamanho)
            cv2.imwrite(caminho_arquivo_dest, frame_dimensionado)
        video.release()
        return sucesso
    except Exception as e:
        print(f"erro {e}")
        return False