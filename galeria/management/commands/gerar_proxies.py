import os
import shutil
import time
from django.core.management.base import BaseCommand
from galeria.models import Midia
from django.conf import settings
import platform
import subprocess
import urllib.request
import zipfile


class Command(BaseCommand):
    help = "Gera proxies H.264 para vídeos e limpa os arquivos de cache antigos"

    def baixar_ffmpeg_win(self):
        self.stdout.write(self.style.WARNING("FFmpeg não encontrado. A transferir e instalar automaticamente para Windows..."))
        url = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
        zip_path = "ffmpeg_temp.zip"
        extract_dir = "ffmpeg_extraido"

        try:
            self.stdout.write("Baixando o zip, isso pode demorar um pouco...")
            urllib.request.urlretrieve(url, zip_path, reporthook=self.mostrar_progresso)
            print()

            self.stdout.write("Extraindo...")
            with zipfile.ZipFile(zip_path,"r") as zip_ref:
                zip_ref.extractall(extract_dir)

            os.makedirs("codec_ffmpeg", exist_ok=True)

            for root, dirs, files in os.walk(extract_dir):
                for file in files:
                    if file in ["ffmpeg.exe","ffprobe.exe"]:
                        caminho_origem = os.path.join(root, file)
                        caminho_destino = os.path.join("codec_ffmpeg",file)
                        shutil.copy2(caminho_origem, caminho_destino)

            self.stdout.write(self.style.SUCCESS("FFmpeg instaldo com sucesso!"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"ERRO ao transferir ffmpeg\nerro:{e}"))
        finally:
            if os.path.exists(zip_path):
                os.remove(zip_path)
            if os.path.exists(extract_dir):
                shutil.rmtree(extract_dir)

    def mostrar_progresso(self, bloco_num, tamanho_bloco, tamanho_total):
        baixado = bloco_num * tamanho_bloco
        porcentagem = baixado * 100 / tamanho_total
        if porcentagem > 100:
            porcentagem = 100
        print(f"\rBaixando o zip... {porcentagem:.1f}% concluído", end="")

    def obter_executavel(self, nome_base):
        if platform.system() == "Windows":
            caminho_local = os.path.join("codec_ffmpeg",f"{nome_base}.exe")
            if not os.path.exists(caminho_local):
                self.baixar_ffmpeg_win()
            return caminho_local
        else:
            # No Linux, testa se o programa está instalado no sistema
            resultado = subprocess.run(['which', nome_base], capture_output=True, text=True)
            if not resultado.stdout.strip():
                self.stdout.write(self.style.ERROR(
                    f"⚠️ {nome_base} não encontrado. No Linux, execute no terminal: sudo apt install ffmpeg"))
            return nome_base

    def obter_codec_video(self, caminho_arquivo):
        comando = [
            self.obter_executavel('ffmpeg'),
            '-v', 'error',
            '-select_streams', 'v:0',
            '-show_entries', 'stream=codec_name',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            caminho_arquivo
        ]
        try:
            resultado = subprocess.run(comando, capture_output=True, text=True, check=True)
            return resultado.stdout.strip().lower()
        except Exception as e:
            return 'hevc'

    def handle(self, *args, **options):
        self.limpar_cache_antigo(horas=1)
        videos = Midia.objects.filter(tipo="video")
        pasta_proxy = os.path.join(settings.MEDIA_ROOT, 'web_proxies')
        os.makedirs(pasta_proxy, exist_ok=True)

        self.stdout.write(self.style.WARNING(f"Iniciando verificação de {videos.count()} vídeos..."))

        for video in videos:
            if not video.caminho_original:
                continue

            caminho_orig = os.path.join(settings.MEDIA_ROOT, str(video.caminho_original))
            nome_base = os.path.basename(caminho_orig).split('.')[0]
            nome_proxy = f"{nome_base}_web.mp4"
            caminho_proxy_full = os.path.join(pasta_proxy, nome_proxy)
            caminho_relativo = f"web_proxies/{nome_proxy}"

            # Se o proxy não existir fisicamente, o FFmpeg entra em ação
            if not os.path.exists(caminho_proxy_full):
                self.stdout.write(f"Convertendo {nome_base} para H.264...")

                comando = [
                    self.obter_executavel('ffmpeg'),
                    '-i', caminho_orig,
                    '-vcodec', 'libx264',
                    '-preset', 'veryfast',
                    '-crf', '32',
                    '-vf', 'scale=-2:1080',
                    '-acodec', 'aac',
                    '-b:a', '96k',
                    '-movflags', '+faststart',
                    '-y',
                    caminho_proxy_full
                ]

                try:
                    subprocess.run(comando, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
                    video.caminho_web = caminho_relativo
                    video.save()
                    self.stdout.write(self.style.SUCCESS(f"✅ {nome_proxy} criado com sucesso!"))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"❌ Erro ao converter: {e}"))
            else:
                # Se o arquivo já existe mas não tá salvo no banco, só atualiza o banco
                if video.caminho_web != caminho_relativo:
                    video.caminho_web = caminho_relativo
                    video.save()

        self.stdout.write(self.style.SUCCESS("Processo de proxies finalizado!"))

    def limpar_cache_antigo(self, horas):
        pasta_proxy = os.path.join(settings.MEDIA_ROOT, 'web_proxies')
        if not os.path.exists(pasta_proxy):
            return

        tempo_agora = time.time()
        limite_segundos = horas * 3600
        apagados = 0

        self.stdout.write(self.style.WARNING(f"Limpando proxies com mais de {horas} hora(s) de vida..."))

        for arquivo in os.listdir(pasta_proxy):
            caminho_arquivo = os.path.join(pasta_proxy, arquivo)

            if os.path.isfile(caminho_arquivo):
                idade_segundos = tempo_agora - os.path.getctime(caminho_arquivo)

                if idade_segundos > limite_segundos:
                    os.remove(caminho_arquivo)
                    apagados += 1
                    # Remove o link do banco de dados para a foto forçar a nova criação
                    Midia.objects.filter(caminho_web=f"web_proxies/{arquivo}").update(caminho_web=None)

        if apagados > 0:
            self.stdout.write(self.style.SUCCESS(f"🧹 Faxina feita! {apagados} proxies antigos foram apagados."))