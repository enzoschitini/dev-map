<!-- Gerado de pages/clean-code/single-responsibility.html por scripts/sync_references.py. Não edite aqui: edite a página e rode o script. -->

# Single Responsibility

*Clean Code / SOLID / Single Responsibility*

Como evitar que uma classe quebre toda vez que qualquer pessoa da empresa muda de ideia, dando a cada motivo de mudança o seu próprio lugar.

<a id="o-problema"></a>
## O problema

Um `Pedido` começa pequeno: itens, cliente, total. Aí alguém precisa salvar o pedido e o método `salvar()` entra na classe. Depois vem o e-mail de confirmação, depois a nota fiscal. Cada método parece natural, porque "tudo isso é do pedido".

**antes — a classe muda por quatro motivos**

```python
class Pedido:
    def __init__(self, itens, cliente):
        self.itens = itens
        self.cliente = cliente

    def total(self):                      # regra de preço (time comercial)
        return sum(i.preco * i.qtd for i in self.itens)

    def salvar(self):                     # SQL (time de dados)
        db.execute("INSERT INTO pedidos (cliente_id, total) VALUES (?, ?)",
                   self.cliente.id, self.total())

    def enviar_confirmacao(self):         # texto e canal (time de marketing)
        smtp.send(self.cliente.email, f"Total do pedido: R$ {self.total():.2f}")

    def gerar_nota(self):                 # regras fiscais (time contábil)
        ...
```

Quatro times diferentes pedem mudanças na mesma classe. O marketing troca o texto do e-mail e o `git blame` do cálculo de preço muda junto. Dois merges na mesma semana conflitam em um arquivo que "ninguém mexeu". E para testar `total()` você precisa importar SMTP e banco, porque eles vieram junto.

<a id="a-ideia"></a>
## A ideia

Uma classe deve ter **um motivo para mudar**. Não "fazer uma coisa só": uma classe pode ter dez métodos. O que conta é quantas pessoas ou áreas diferentes podem pedir mudança nela por razões diferentes. Cada razão ganha uma classe.

| Quem pede a mudança | O que muda | Onde passa a morar |
|---|---|---|
| Comercial | Como o total é calculado | `Pedido` |
| Dados | Tabela, colunas, banco | `RepositorioDePedidos` |
| Marketing | Texto e canal do aviso | `Confirmacao` |
| Contabilidade | Layout e regras da nota | `EmissorDeNota` |

O ponto é a pergunta que você faz: não "o que essa classe faz?", e sim *"quem vai me pedir para mexer aqui, e por quê?"*. Se a resposta tem mais de um nome, a classe tem mais de uma responsabilidade.

<a id="depois"></a>
## Como fica

```python
# 1. a regra de negócio: só dados e cálculo, nada de infraestrutura
class Pedido:
    def __init__(self, itens, cliente):
        self.itens = itens
        self.cliente = cliente

    def total(self):
        return sum(i.preco * i.qtd for i in self.itens)

# 2. persistência: só muda se o banco mudar
class RepositorioDePedidos:
    def salvar(self, pedido):
        db.execute("INSERT INTO pedidos (cliente_id, total) VALUES (?, ?)",
                   pedido.cliente.id, pedido.total())

# 3. comunicação: só muda se o texto ou o canal mudar
class Confirmacao:
    def enviar(self, pedido):
        smtp.send(pedido.cliente.email, f"Total do pedido: R$ {pedido.total():.2f}")

# 4. quem junta as peças fica fora das três
def fechar_pedido(pedido, repositorio, confirmacao):
    repositorio.salvar(pedido)
    confirmacao.enviar(pedido)
```

> **Dica.** O teste de `total()` agora é uma linha: cria um `Pedido` com dois itens e confere a soma. Nenhum banco, nenhum SMTP, nenhum mock.

<a id="como-reconhecer"></a>
## Como reconhecer a violação

Raramente o problema aparece como "a classe faz muita coisa". Aparece como sintomas no dia a dia:

| Sintoma | O que está acontecendo |
|---|---|
| Nome com `Manager`, `Helper`, `Utils` ou "`E`" no meio (`ValidaESalva`) | O nome não consegue dizer uma coisa só porque ela não é uma coisa só |
| Imports de mundos distantes no mesmo arquivo: `sqlalchemy`, `smtplib`, `reportlab` | A classe fala com banco, rede e disco além da regra |
| Grupos de métodos que usam atributos diferentes | Há duas classes escondidas dentro de uma |
| Conflito de merge sempre no mesmo arquivo, por pessoas de áreas diferentes | Vários atores pedem mudança no mesmo lugar |
| Teste unitário que precisa de mock de tudo | O que você quer testar está preso ao que não quer |

<a id="quando-nao-aplicar"></a>
## Quando não aplicar

O custo é real: mais classes, mais arquivos e um lugar a mais para olhar para entender um fluxo. Vale pagar quando as razões de mudança **existem de fato** e já se cruzaram, não quando você imagina que talvez existam.

| Situação | Por que não | Faça isto |
|---|---|---|
| Classe pequena e coesa, que só tem um ator por trás | Dividir não elimina nenhuma mudança cruzada, só distribui o código | Deixe como está |
| Script de uma vez, ou protótipo | O custo de separar supera o de mexer três linhas depois | Escreva junto; separe quando o segundo ator aparecer |
| Um método de seis linhas que "faz duas coisas" | Um método não é uma responsabilidade; uma função de seis linhas lê melhor inteira | Extraia só se um dos pedaços for reutilizado |

> **Perigo.** O exagero comum: uma classe por verbo (`CalculadorDeTotal`, `SomadorDeItens`, `FormatadorDeMoeda`), cada uma com um método `executar()`. Para entender um pedido você abre doze arquivos. Responsabilidade é um *motivo de mudança*, não um verbo.

<a id="relacao"></a>
## Relação com os outros

A saída de uma classe grande quase sempre é composição: o `fechar_pedido` acima é um pequeno [Facade](estruturais/facade/explicacao.md). Quando o que muda dentro de uma responsabilidade é o *jeito* de fazer, entra o [Strategy](comportamentais/strategy/explicacao.md). E o que impede `Confirmacao` de conhecer o SMTP direto é o [Dependency Inversion](dependency-inversion.md).
