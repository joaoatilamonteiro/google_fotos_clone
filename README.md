# AdomoFotos — Galeria de Fotos e Vídeos

Um "Google Fotos" caseiro, feito em Django, para organizar, importar e visualizar fotos e vídeos armazenados localmente — com extração automática de metadados (EXIF, GPS, pessoas marcadas no Google Takeout), geração de miniaturas e proxies de vídeo otimizados para web.

## Funcionalidades

- **Importação automática de mídias** a partir de uma pasta do HD (`importar_midia`), com:
  - Cálculo de hash SHA-256 para evitar duplicatas.
  - Extração de metadados EXIF (data, modelo do celular, dimensões, orientação, GPS).
  - Leitura de arquivos `.json` do Google Takeout (pessoas marcadas, data de captura, geolocalização).
  - Reconhecimento de datas a partir do nome do arquivo (padrões WhatsApp e câmera comum) quando não há EXIF.
  - Geocodificação reversa (cidade/estado/país) e detecção de fuso horário a partir das coordenadas GPS.
  - Organização automática dos arquivos originais em `media/originais/AAAA/MM/`.
  - Geração de miniaturas quadradas para fotos e vídeos.
- **Geração de proxies de vídeo** (`gerar_proxies`): converte vídeos para H.264/MP4 leve (via FFmpeg) para reprodução fluida no navegador, com download automático do FFmpeg no Windows quando necessário.
- **Galeria web** com rolagem infinita (HTMX), exibindo fotos e vídeos em grade, com modal (lightbox) para visualização em tamanho grande, suporte a conversão de HEIC no navegador e player de vídeo.
- **Cadastro de pessoas** reconhecidas automaticamente a partir dos metadados do Google Takeout.

## 🛠️ Stack Técnica

- **Backend:** Python + Django 6.0
- **Banco de dados:** SQLite
- **Frontend:** HTML + CSS + [HTMX](https://htmx.org/) (rolagem infinita) + [heic2any](https://github.com/alexcorvi/heic2any) (conversão de HEIC no navegador)
- **Processamento de mídia:**
  - [Pillow](https://python-pillow.org/) + `pillow-heif` — leitura de imagens e EXIF, geração de miniaturas
  - [OpenCV](https://opencv.org/) (`cv2`) — extração de frame de vídeos para miniatura
  - [pymediainfo](https://github.com/sbraz/pymediainfo) — metadados de vídeo
  - [FFmpeg](https://ffmpeg.org/) — geração de proxies de vídeo em H.264
  - [TimezoneFinder](https://github.com/jannikmi/timezonefinder) — fuso horário a partir de coordenadas GPS
  - [Geopy](https://geopy.readthedocs.io/) (Nominatim) — geocodificação reversa (endereço a partir de GPS)

## 📁 Estrutura do Projeto

```
adomofotos/              # Configurações do projeto Django (settings, urls, wsgi/asgi)
galeria/                 # App principal
├── models.py            # Modelos: Midia, Pessoa, Rosto
├── views.py             # View da galeria (com suporte a paginação via HTMX)
├── urls.py               # Rotas do app
├── utils.py              # Funções de extração de metadados, hash e miniaturas
├── admin.py
├── templates/galeria/    # home.html (página principal) e lista_midias.html (parcial HTMX)
└── management/commands/
    ├── importar_midia.py  # Comando de importação de fotos/vídeos
    └── gerar_proxies.py   # Comando de geração de proxies de vídeo
manage.py
reset.bat                 # Script (Windows) para resetar o banco e reimportar tudo
```

## 🗃️ Modelo de Dados

- **Midia**: arquivo (foto ou vídeo) com hash único, caminhos (original, miniatura, proxy web), metadados (data, celular, dimensões, orientação, fuso horário, local) e pessoas associadas.
- **Pessoa**: nome de uma pessoa reconhecida nos metadados.
- **Rosto**: relação entre uma mídia e uma pessoa (estrutura preparada para reconhecimento facial).

## 🚀 Como Rodar

### Pré-requisitos

- Python 3.12+
- FFmpeg instalado no PATH (necessário para gerar proxies de vídeo; no Windows o comando `gerar_proxies` tenta baixar automaticamente)

### Instalação

```bash
# Crie e ative um ambiente virtual
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/Mac
source .venv/bin/activate

# Instale as dependências
pip install django pillow pillow-heif opencv-python pymediainfo timezonefinder geopy pytz
```

> ⚠️ Este projeto ainda não possui um arquivo `requirements.txt`. Recomenda-se criar um com `pip freeze > requirements.txt` após instalar as dependências.

### Configuração e execução

```bash
# Aplique as migrações
python manage.py makemigrations
python manage.py migrate

# Importe suas fotos e vídeos de uma pasta local
python manage.py importar_midia "CAMINHO/PARA/SUAS/FOTOS" --destino nome_do_lote

# Gere os proxies de vídeo otimizados para web
python manage.py gerar_proxies

# Suba o servidor de desenvolvimento
python manage.py runserver
```

Depois é só acessar `http://127.0.0.1:8000/` no navegador.

No Windows, o script `reset.bat` automatiza todo esse fluxo (apaga o banco, recria, importa e gera proxies) para um caminho de pasta fixo — ajuste o caminho dentro do arquivo antes de usar.

## 📝 Notas

- O projeto está configurado com `DEBUG = True` e uma `SECRET_KEY` de desenvolvimento — **não usar em produção sem antes revisar as configurações de segurança** (`ALLOWED_HOSTS`, `DEBUG`, `SECRET_KEY`, etc.).
- Os arquivos de mídia processados ficam salvos em `media/`, fora do controle de versão.
