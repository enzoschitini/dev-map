<!-- Gerado de pages/clean-code/liskov-substitution.html por scripts/sync_references.py. Não edite aqui: edite a página e rode o script. -->

# Liskov Substitution

*Clean Code / SOLID / Liskov Substitution*

Como garantir que uma subclasse pode entrar no lugar da classe base sem que quem chama precise perguntar "que tipo você é?".

<a id="o-problema"></a>
## O problema

Um sistema de pagamentos tem a classe base `Pagamento` com o método `estornar()`. O cartão e o Pix estornam. Aí chega o boleto, que **não tem estorno**: depois de pago, o dinheiro já foi para o outro lado. A saída rápida é herdar mesmo assim e lançar um erro.

**antes — a subclasse promete o que não cumpre**

```python
class Pagamento:
    def estornar(self):
        gateway.estornar(self.id)

class PagamentoBoleto(Pagamento):
    def estornar(self):
        raise NotImplementedError("boleto não estorna")

# quem chama, sem suspeitar de nada:
def cancelar_compra(pagamentos):
    for p in pagamentos:
        p.estornar()          # estoura no meio da lista, com metade já estornada
```

O sistema de tipos diz que `PagamentoBoleto` é um `Pagamento`. O comportamento diz que não é. O resultado é um erro em produção, no meio de um laço, com parte dos pagamentos já estornados. E o próximo desenvolvedor aprende a lição errada: escrever `if not isinstance(p, PagamentoBoleto)` antes de cada chamada.

<a id="a-ideia"></a>
## A ideia

Onde o código espera um `Pagamento`, qualquer subclasse tem que funcionar **sem surpresa**. Isso não é sobre tipos: é sobre o *contrato* que a classe base promete. A subclasse pode fazer mais, mas não pode fazer menos nem de outro jeito.

| Regra do contrato | Em palavras | Quebra quando |
|---|---|---|
| Pré-condições não ficam mais fortes | A subclasse aceita tudo o que a base aceitava | Passa a rejeitar valores que a base aceitava |
| Pós-condições não ficam mais fracas | A subclasse entrega tudo o que a base prometia | Devolve `None`, ou deixa de fazer o efeito prometido |
| Nada de erro novo | As falhas possíveis são as da base | Lança uma exceção que a base nunca lançou |
| Invariantes se mantêm | O que é sempre verdade na base continua verdade | Deixa o objeto num estado que a base proibia |

O ponto é a direção da pergunta. Não é "o boleto é um pagamento?" (no mundo real, é), e sim *"o boleto cumpre tudo o que o código promete a quem usa um pagamento?"*. Se não cumpre, a herança está errada, mesmo que o nome pareça certo.

<a id="depois"></a>
## Como fica

Se só alguns pagamentos estornam, `estornar` não pertence à base. Ele vira uma capacidade separada, e quem precisa estornar pede **essa capacidade**, não "um pagamento":

```python
from typing import Protocol

# 1. a base só promete o que todos cumprem
class Pagamento:
    def __init__(self, id, valor):
        self.id = id
        self.valor = valor

# 2. estornar é uma capacidade, não uma obrigação de todos
class Estornavel(Protocol):
    def estornar(self) -> None: ...

class PagamentoCartao(Pagamento):
    def estornar(self):
        gateway.estornar(self.id)

class PagamentoBoleto(Pagamento):
    pass                               # sem estornar(), sem mentira

# 3. quem chama pede exatamente o que usa
def estornar_todos(pagamentos: list[Estornavel]):
    for p in pagamentos:
        p.estornar()
```

> **Dica.** Agora tentar estornar um boleto é um erro **de tipo**, visto no editor ou na CI, e não um erro de execução às três da manhã. Quando o contrato está certo, o compilador (ou o verificador de tipos) passa a trabalhar a seu favor.

<a id="como-reconhecer"></a>
## Como reconhecer a violação

| Sintoma | O que está acontecendo |
|---|---|
| `raise NotImplementedError` ou `throw new Error("não suportado")` numa sobrescrita | A subclasse recusa parte do contrato que herdou |
| Método sobrescrito vazio, ou que só devolve um valor "neutro" | A promessa foi esvaziada em silêncio, o que é pior que um erro |
| `isinstance` / `instanceof` / `type(x) == …` em quem usa a base | Quem chama já aprendeu que não pode confiar na base |
| Subclasse que valida mais que a base (`if valor > 1000: raise`) | Pré-condição ficou mais forte |
| Classe base com um comentário "não chamar em subclasse X" | A exceção está documentada em vez de modelada |

<a id="quando-nao-aplicar"></a>
## Quando não é o problema

Liskov não proíbe herança. Proíbe herança que **mente**. Em dois casos o instinto de "isso viola Liskov" é falso alarme:

| Situação | Por que está tudo bem |
|---|---|
| A subclasse faz *mais* que a base: aceita mais entradas, devolve um tipo mais específico | Quem chama a base nunca vai notar; a regra só proíbe fazer menos |
| A subclasse muda o jeito, mas cumpre o contrato (cache, log, outro algoritmo) | É exatamente a variação que a abstração existe para permitir |

> **Cuidado.** O exemplo clássico do `Quadrado` que herda de `Retangulo` falha pelo mesmo motivo: `set_largura` numa base promete "a altura não muda", e o quadrado não pode cumprir. Matematicamente é um retângulo; *como contrato de objeto mutável*, não é.

<a id="relacao"></a>
## Relação com os outros

Liskov é o que torna o [Open/Closed](open-closed.md) seguro: só dá para estender por subclasse se a subclasse for substituível. Quando a solução é separar a capacidade em uma interface própria, como acima, você está a um passo do [Interface Segregation](interface-segregation.md). Em linguagens com herança rasa, a correção costuma ser trocar herança por [composição](estruturais/decorator/explicacao.md).
