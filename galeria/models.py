from django.db import models


#criando o modelo da tabela do sql
class Midia(models.Model):
    id_hash_arquivo = models.CharField(max_length=64, unique=True)
    caminho_original = models.CharField(max_length=500)
    caminho_thumb = models.CharField(max_length=500)

    #criacao de coluna para videos
    tipo = models.CharField(max_length=10, default='')
    duracao = models.FloatField(null= True, blank=True)

    #metadados
    data = models.DateTimeField(null=True, blank=True)
    fuso_horario = models.CharField(max_length=50,null=True, blank=True )
    celular = models.CharField(max_length=50, null= True, blank= True)
    local = models.CharField(max_length=200, null=True, blank=True)

    largura = models.IntegerField(null=True,blank=True)
    altura = models.IntegerField(null=True,blank=True)
    orientacao = models.CharField(max_length=14, null=True, blank=True)
    pessoas = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return f"Foto está no caminho {self.caminho_original}"

class Pessoa(models.Model):
    nome = models.CharField(max_length=50, null=True, blank=True)

    def __str__(self):
        return self.nome if self.nome else f"Pessoa desconhecida #{self.id}"

class Rosto(models.Model):
    assinatura = models.CharField(max_length=100)

    foto = models.ForeignKey(Midia, on_delete=models.CASCADE, related_name="rostos")
    pessoa = models.ForeignKey(Pessoa, on_delete=models.SET_NULL, null=True, blank=True, related_name="rostos")

    def __str__(self):
        return f"Rosto na foto {self.foto.id}"

