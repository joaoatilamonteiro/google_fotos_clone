import os
from datetime import datetime
from django.core.management.base import BaseCommand
from django.utils.timezone import make_aware
from galeria.models import Midia, Pessoa
from galeria.utils import gerar_hash, extrai_metadados_foto, cria_miniatura_foto, cria_miniatura_video, extrai_metadados_video, json_takeout_leitura
import pytz
import re
import shutil


def extrai_nome_wpp(nome_arquivo):
    # 1. Caça o padrão WhatsApp: "WhatsApp Image 2026-04-19 at 21.00.44.jpeg"
    match_wpp = re.search(r"(\d{4}-\d{2}-\d{2}) at (\d{2}\.\d{2}\.\d{2})", nome_arquivo)
    if match_wpp:
        data_str = f"{match_wpp.group(1)} {match_wpp.group(2)}"
        try:
            return datetime.strptime(data_str, "%Y-%m-%d %H.%M.%S")
        except:
            pass

    # 2. Caça o padrão Câmera comum (Samsung/iPhone): "20260714_123255.heic"
    match_padrao = re.search(r"(\d{8})_(\d{6})", nome_arquivo)
    if match_padrao:
        try:
            return datetime.strptime(f"{match_padrao.group(1)}_{match_padrao.group(2)}", "%Y%m%d_%H%M%S")
        except:
            pass

    return None

def organiza_arquivo(caminho_antigo, data_captura):
    ano = data_captura.strftime("%Y")
    mes = data_captura.strftime("%m")
    nome_arquivo = os.path.basename(caminho_antigo)

    pasta_destino = os.path.join("media","originais",ano,mes)
    os.makedirs(pasta_destino, exist_ok=True)
    caminho_novo = os.path.join(pasta_destino, nome_arquivo)

    if not os.path.exists(caminho_novo):
        shutil.copy2(caminho_antigo,caminho_novo)
    return f"originais/{ano}/{mes}/{nome_arquivo}"

def processa_foto(caminho_original, hash_arquivo, subpasta):
    pasta_destino_miniaturas = os.path.join("media", subpasta,"fotos")
    os.makedirs(pasta_destino_miniaturas, exist_ok=True)

    dados_takeout = json_takeout_leitura(caminho_original)
    #verificacao de dados
    dados_exif = extrai_metadados_foto(caminho_original)
    data_captura = dados_exif.get('data')

    if not data_captura:
        data_captura = extrai_nome_wpp(os.path.basename(caminho_original))

    if not data_captura:
        data_captura = dados_takeout.get('data_captura')

    if not data_captura:
        timestamp_arquivo = os.path.getctime(caminho_original)
        data_captura = datetime.fromtimestamp(timestamp_arquivo)

    if data_captura.tzinfo is None:

        if dados_exif.get("fuso_horario"):
            fuso_correto = pytz.timezone(dados_exif.get("fuso_horario"))
            data_captura = fuso_correto.localize(data_captura)
        else:
            data_captura = make_aware(data_captura)
    caminho_salvo_banco = organiza_arquivo(caminho_original, data_captura)

    #fim da verificacao
    nome_miniatura = f"{hash_arquivo}.jpg"
    caminho_miniatura = os.path.join(pasta_destino_miniaturas, nome_miniatura)

    sucesso_miniatura = cria_miniatura_foto(caminho_original, caminho_miniatura)
    caminho_salvar = f"{subpasta}/fotos/{nome_miniatura}" if sucesso_miniatura else ""

    Midia.objects.create(
        tipo = "foto",
        caminho_original=caminho_salvo_banco,
        caminho_thumb=caminho_salvar,
        id_hash_arquivo=hash_arquivo,
        data=data_captura,
        celular=dados_exif.get('celular'),
        largura = dados_exif.get("largura_pixel"),
        altura = dados_exif.get("altura_pixel"),
        orientacao = dados_exif.get("orientacao"),
        fuso_horario = dados_exif.get("fuso_horario"),
        local=dados_exif.get("local"),
        pessoas = dados_takeout.get("pessoas")
    )
    nomes_json = dados_takeout.get("pessoas")
    if nomes_json:
        for nome_pessoa in nomes_json:
            # get_or_create procura a pessoa. Se não existir, ele cria na hora!
            Pessoa.objects.get_or_create(nome=nome_pessoa)

    return os.path.basename(caminho_original)


def processa_video(caminho_original, hash_arquivo, subpasta):
    pasta_destino_miniaturas = os.path.join("media", subpasta, "videos")
    os.makedirs(pasta_destino_miniaturas, exist_ok=True)
    dados_takeout = json_takeout_leitura(caminho_original)

    dados_video = extrai_metadados_video(caminho_original)

    # Verifica se a data existe e se é uma string antes de tentar usar o [:19]
    if dados_video["data"] and isinstance(dados_video["data"], str):
        data_captura = datetime.strptime(dados_video["data"][:19], '%Y-%m-%d %H:%M:%S')
    else:
        data_captura = None

    if not data_captura:
        data_captura = dados_takeout.get('data_captura')

    if not data_captura:
        data_captura = extrai_nome_wpp(os.path.basename(caminho_original))
    if not data_captura:
        timestamp_arquivo = os.path.getctime(caminho_original)
        data_captura = datetime.fromtimestamp(timestamp_arquivo)

    if data_captura.tzinfo is None:
        data_captura = make_aware(data_captura)
    caminho_salvo_banco = organiza_arquivo(caminho_original, data_captura)  # <--- AQUI NA FOTO TEM

    nome_miniatura = f"{hash_arquivo}.jpg"
    caminho_miniatura = os.path.join(pasta_destino_miniaturas, nome_miniatura)

    sucesso_miniatura = cria_miniatura_video(caminho_original, caminho_miniatura)
    caminho_salvar = f"{subpasta}/videos/{nome_miniatura}" if sucesso_miniatura else ""

    Midia.objects.create(
        tipo = "video",
        caminho_original=caminho_salvo_banco,
        caminho_thumb=caminho_salvar,
        id_hash_arquivo=hash_arquivo,
        data=data_captura,
        celular=dados_video.get("celular") or "Desconhecido",
        altura=dados_video.get("altura_pixel"),
        largura=dados_video.get("largura_pixel"),
        duracao = dados_video.get("duracao"),
        pessoas = dados_takeout.get("pessoas")
    )

    nomes_json = dados_takeout.get("pessoas")
    if nomes_json:
        for nome_pessoa in nomes_json:
            # get_or_create procura a pessoa. Se não existir, ele cria na hora!
            Pessoa.objects.get_or_create(nome=nome_pessoa)

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