from django.shortcuts import render
from django.core.paginator import Paginator  # Importamos o fatiador do Django
from .models import Midia


def galeria_home(request):
    midias_lista = Midia.objects.all().order_by('-data')

    # Fatiador: Vamos mandar 40 fotos por vez
    paginator = Paginator(midias_lista, 40)

    # Olha na URL qual é a página que o HTMX está pedindo (se não tiver, é a 1)
    numero_pagina = request.GET.get('page', 1)
    page_obj = paginator.get_page(numero_pagina)

    # Se a requisição veio do HTMX (o usuário rolou a tela)
    if request.headers.get('HX-Request'):
        # Retorna SÓ o pedaço de HTML com as novas fotos
        return render(request, 'galeria/lista_midias.html', {'page_obj': page_obj})

    # Se for o carregamento normal (usuário abriu o site pela primeira vez)
    contexto = {
        'page_obj': page_obj,
        'total_midias': midias_lista.count()  # Para o nosso contador não quebrar
    }
    return render(request, 'galeria/home.html', contexto)
