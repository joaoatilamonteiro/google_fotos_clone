import os
from datetime import datetime
from django.core.management.base import BaseCommand
from django.utils.timezone import make_aware
from galeria.models import Midia
from galeria.utils import gerar_hash, extrai_metadados, cria_miniatura_foto, cria_miniatura_video

def processa_foto(caminho_original, hash_arquivo, subpasta):
    pasta_destino_miniaturas = os.path.join("media", subpasta)
    os.makedirs(pasta_destino_miniaturas, exist_ok=True)

    dados_exif = extrai_metadados(caminho_original)
    data_captura = dados_exif.get('data')
    if not data_captura:
        timestamp_arquivo = os.path.getctime(caminho_original)
        data_captura = datetime.fromtimestamp(timestamp_arquivo)

    if data_captura.tzinfo is None:
        data_captura = make_aware(data_captura)

    nome_miniatura = f"{hash_arquivo}.jpg"
    caminho_miniatura = os.path.join(pasta_destino_miniaturas, nome_miniatura)

    sucesso_miniatura = cria_miniatura_foto(caminho_original, caminho_miniatura)
    caminho_salvar = f"{subpasta}/{nome_miniatura}" if sucesso_miniatura else ""

    Midia.objects.create(
        caminho_original=caminho_original,
        caminho_thumb=caminho_salvar,
        id_hash_arquivo=hash_arquivo,
        data=data_captura,
        celular=dados_exif.get('celular')
    )

    return os.path.basename(caminho_original)


def processa_video(caminho_original, hash_arquivo, subpasta):
    pasta_destino_miniaturas = os.path.join("media", subpasta)
    os.makedirs(pasta_destino_miniaturas, exist_ok=True)

    timestamp_arquivo = os.path.getctime(caminho_original)
    data_captura = datetime.fromtimestamp(timestamp_arquivo)

    if data_captura.tzinfo is None:
        data_captura = make_aware(data_captura)

    nome_miniatura = f"{hash_arquivo}.jpg"
    caminho_miniatura = os.path.join(pasta_destino_miniaturas, nome_miniatura)

    sucesso_miniatura = cria_miniatura_video(caminho_original, caminho_miniatura)
    caminho_salvar = f"{subpasta}/{nome_miniatura}" if sucesso_miniatura else ""

    Midia.objects.create(
        caminho_original=caminho_original,
        caminho_thumb=caminho_salvar,
        id_hash_arquivo=hash_arquivo,
        data=data_captura,
        celular='Desconhecido'
    )

    return os.path.basename(caminho_original)

class Command(BaseCommand):
    help = "Vasculha uma pasta do hd, processa fotos e vídeos e salva no banco de dados"

    def add_arguments(self, parser):
        parser.add_argument("pasta_origem", type=str, help="Caminho completo com suas mídias originais")
        parser.add_argument("--destino", type=str, help="Nome da subpasta dentro da pasta media", default=["miniatura"],
                            nargs="+")

    def handle(self, *args, **kwargs):
        # CORREÇÃO: Extraindo as variáveis do kwargs corretamente
        pasta_origem = kwargs["pasta_origem"]
        subpasta = "_".join(kwargs["destino"])

        # CORREÇÃO: Iniciando os contadores antes do loop
        fotos_salvas = 0
        videos_salvos = 0
        itens_ignorados = 0

        if not os.path.exists(pasta_origem):
            self.stdout.write(self.style.ERROR(f"A pasta {pasta_origem} não existe."))
            return

        self.stdout.write(self.style.SUCCESS(f"Iniciando varredura na pasta {pasta_origem}..."))

        for diretorio_atual, subdiretorios, arquivos in os.walk(pasta_origem):
            for arquivo in arquivos:

                caminho_completo = os.path.join(diretorio_atual, arquivo)
                nome_arquivo, extensao = os.path.splitext(arquivo)
                extensao = extensao.lower()

                hash_arquivo = gerar_hash(caminho_completo)

                if not hash_arquivo:
                    self.stdout.write(self.style.ERROR(f"Erro de leitura: {arquivo}"))
                    itens_ignorados += 1
                    continue

                if Midia.objects.filter(id_hash_arquivo=hash_arquivo).exists():
                    self.stdout.write(self.style.WARNING(f"Duplicata ignorada: {arquivo}"))
                    itens_ignorados += 1
                    continue

                try:
                    if extensao in [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".webp", ".heic", ".raw", ".svg",".heic"]:
                        nome_arq = processa_foto(caminho_completo, hash_arquivo, subpasta)
                        self.stdout.write(self.style.SUCCESS(f"[FOTO] Importada: {nome_arq}"))
                        fotos_salvas += 1

                    elif extensao in [".mp4", ".avi", ".mov", ".wmv", ".flv", ".mkv", ".webm", ".mpeg", ".3gp", ".ogg"]:
                        nome_arq = processa_video(caminho_completo, hash_arquivo, subpasta)
                        self.stdout.write(self.style.SUCCESS(f"[VÍDEO] Importado: {nome_arq}"))
                        videos_salvos += 1

                    else:
                        self.stdout.write(self.style.NOTICE(f"[IGNORADO] Formato não suportado: {arquivo}"))
                        itens_ignorados += 1

                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"[ERRO] Falha ao processar {arquivo}: {str(e)}"))

        # ==========================================
        # 3. RELATÓRIO FINAL
        # ==========================================
        self.stdout.write(self.style.SUCCESS("\n--- VARREDURA CONCLUÍDA ---"))
        self.stdout.write(self.style.SUCCESS(f"Fotos importadas: {fotos_salvas}"))
        self.stdout.write(self.style.SUCCESS(f"Vídeos importados: {videos_salvos}"))
        self.stdout.write(self.style.WARNING(f"Arquivos ignorados/duplicados: {itens_ignorados}"))
        self.stdout.write(self.style.WARNING(f"Caminho mapeado: {pasta_origem}"))

        data_atual = datetime.now().strftime("%d%m%Y_%H%M%S")
        nome_relatorio = f"relatorio_{subpasta}.txt"

        with open(nome_relatorio, "w+", encoding="utf-8") as arquivo_txt:
            arquivo_txt.write("--- RELATÓRIO MULTIMÍDIA DE IMPORTAÇÃO ---\n")
            arquivo_txt.write(f"Data da execução: {data_atual}\n")
            arquivo_txt.write(f"Caminho mapeado: {pasta_origem}\n")
            arquivo_txt.write(f"Fotos importadas com sucesso: {fotos_salvas}\n")
            arquivo_txt.write(f"Vídeos importados com sucesso: {videos_salvos}\n")
            arquivo_txt.write(f"Arquivos ignorados (duplicados/inválidos): {itens_ignorados}\n")
            arquivo_txt.write("------------------------------------------\n")

        self.stdout.write(self.style.SUCCESS(f"\n[!] Relatório salvo como: {nome_relatorio} na raiz do projeto."))