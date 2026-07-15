import os
from datetime import datetime
from django.core.management.base import BaseCommand
from django.utils.timezone import make_aware
from galeria.models import Midia
from galeria.utils import gerar_hash, extrai_metadados, cria_miniatura


class Command(BaseCommand):
    help = "Vasculha uma pasta do hd, processa as fotos tirando informações dos metadados e salva no banco de dados"

    def add_arguments(self, parser):
        parser.add_argument("pasta_origem", type=str, help="caminho completo com suas fotos originais")
        parser.add_argument("--destino",type=str, help = "Nome da subpasta que ficará dentro da pasta media", default=["miniatura"],nargs="+")

    def handle(self, *args, **kwargs):
        pasta_origem = kwargs["pasta_origem"]
        fotos_salvas = 0
        fotos_ignoradas = 0
        extensoes_validas = ('.jpg', '.jpeg', '.png')

        subpasta = " ".join(kwargs["destino"])
        pasta_destino_miniaturas = os.path.join("media", subpasta)
        self.stdout.write(self.style.SUCCESS(f"iniciando varredura na pasta {pasta_origem}"))

        for diretorio_atual, subdiretorios, arquivos in os.walk(pasta_origem):
            for nome_arquivo in arquivos:

                if nome_arquivo.lower().endswith(extensoes_validas):
                    caminho_completo = os.path.join(diretorio_atual, nome_arquivo)

                    hash_foto = gerar_hash(caminho_completo)

                    if not hash_foto:
                        self.stdout.write(self.style.ERROR(f"Erro de leitura: {nome_arquivo}"))
                        continue

                    # CORREÇÃO: Buscando pelo nome correto da coluna (id_hash_arquivo)
                    if Midia.objects.filter(id_hash_arquivo=hash_foto).exists():
                        self.stdout.write(self.style.WARNING(f"Duplicata ignorada: {nome_arquivo}"))
                        fotos_ignoradas += 1
                        continue

                    dados_exif = extrai_metadados(caminho_completo)

                    data_captura = dados_exif.get('data')
                    if not data_captura:
                        timestamp_arquivo = os.path.getctime(caminho_completo)
                        data_captura = datetime.fromtimestamp(timestamp_arquivo)

                    if data_captura.tzinfo is None:
                        data_captura = make_aware(data_captura)

                    nome_miniatura = f"{hash_foto}.jpg"
                    caminho_miniatura = os.path.join(pasta_destino_miniaturas, nome_miniatura)

                    sucesso_miniatura = cria_miniatura(caminho_completo, caminho_miniatura)
                    caminho_salvar = f"{subpasta}/{nome_miniatura}" if sucesso_miniatura else ""

                    # CORREÇÃO: Salvando usando os nomes exatos do seu models.py
                    Midia.objects.create(
                        caminho_original=caminho_completo,
                        caminho_thumb=caminho_salvar,  # Antes era 'miniatura'
                        id_hash_arquivo=hash_foto,  # Antes era 'hash_arquivo'
                        data=data_captura,  # Antes era 'data_captura'
                        celular=dados_exif.get('celular')  # Antes era 'modelo_camera'
                    )

                    self.stdout.write(self.style.SUCCESS(f"[+] Importada: {nome_arquivo}"))
                    fotos_salvas += 1

        self.stdout.write(self.style.SUCCESS("\n--- VARREDURA CONCLUÍDA ---"))
        self.stdout.write(self.style.SUCCESS(f"Novas fotos no sistema: {fotos_salvas}"))
        self.stdout.write(self.style.WARNING(f"Duplicatas barradas: {fotos_ignoradas}"))
        self.stdout.write(self.style.WARNING(f"Caminho completo da pasta: {pasta_origem}"))

        data_atual = datetime.now().strftime("%d%m%Y_%H%M%S")
        nome_relatorio = f"relatorio_{subpasta}.txt"

        with open(nome_relatorio, "w+", encoding="utf-8") as arquivo:
            arquivo.write("--- RELATÓRIO DE IMPORTAÇÃO ---\n")
            arquivo.write(f"Data da execução: {data_atual}\n")
            arquivo.write(f"Caminho mapeado: {pasta_origem}\n")
            arquivo.write(f"Fotos importadas com sucesso: {fotos_salvas}\n")
            arquivo.write(f"Fotos ignoradas (duplicadas): {fotos_ignoradas}\n")
            arquivo.write("-------------------------------\n")
        self.stdout.write(self.style.SUCCESS(f"\n[!] Relatório salvo como: {nome_relatorio} na raiz do projeto."))