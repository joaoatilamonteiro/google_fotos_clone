import os
import time
import subprocess
from django.core.management.base import BaseCommand
from galeria.models import Midia
from django.conf import settings


class Command(BaseCommand):
    help = "Gera proxies H.264 para vídeos e limpa os arquivos de cache antigos"

    def handle(self, *args, **options):
        # =======================================================
        # ÁREA DE TESTE: RESET DE 1 HORA
        # Para desativar a exclusão, basta comentar a linha abaixo:
        self.limpar_cache_antigo(horas=1)
        # =======================================================

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
                    'ffmpeg',
                    '-i', caminho_orig,
                    '-vcodec', 'libx264',  # Formato universal da web
                    '-preset', 'fast',  # Conversão rápida
                    '-crf', '28',  # Qualidade equilibrada
                    '-acodec', 'aac',  # Áudio universal
                    '-y',  # Sobrescrever se necessário
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
        """Apaga vídeos web criados há mais de 'X' horas e limpa do banco de dados"""
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