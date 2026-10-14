<!-- Gerado de pages/clean-code/dependency-inversion.html por scripts/sync_references.py. Não edite aqui: edite a página e rode o script. -->

# Dependency Inversion

*Clean Code / SOLID / Dependency Inversion*

Como fazer a regra de negócio mandar na infraestrutura, e não o contrário, para trocar banco, e-mail ou relógio sem tocar nas regras.

<a id="o-problema"></a>
## O problema

A regra "ao confirmar um pedido, salvar e avisar o cliente" é a parte que vale dinheiro. Mas, escrita de forma direta, ela cria o MySQL e o SMTP ali mesmo, dentro do método:

**antes — a regra de negócio constrói a infraestrutura**

```python
class ConfirmarPedido:
    def executar(self, pedido):
        banco = mysql.connect(host="db.interno", user="app")   # a regra sabe o host
        banco.execute("UPDATE pedidos SET status='ok' WHERE id=%s", pedido.id)

        smtp = smtplib.SMTP("smtp.empresa.com")              # e o servidor de e-mail
        smtp.sendmail("loja@empresa.com", pedido.email, "Confirmado")
```

A regra mais importante do sistema depende de detalhes que mudam o tempo todo: onde está o banco, qual servidor de e-mail, qual biblioteca. Para testá-la, é preciso um MySQL e um SMTP de verdade. Trocar para PostgreSQL ou para um serviço de e-mail exige editar a regra, e o teste dela quebra por um motivo que não tem nada a ver com a regra.

<a id="a-ideia"></a>
## A ideia

O princípio tem duas metades:

1. Módulos de alto nível (a regra) não dependem de módulos de baixo nível (banco, e-mail). **Os dois dependem de abstrações.**
2. As abstrações não dependem de detalhes; **os detalhes dependem das abstrações.**

Por isso "inversão": no código original, a seta de dependência vai da regra para o MySQL. Depois da inversão, o MySQL é que aponta para uma interface **que a regra definiu**. A regra passa a ser dona da interface, e a infraestrutura vira um plugin.

| Peça | Papel | No exemplo |
|---|---|---|
| Alto nível | A regra, que decide o que precisa | `ConfirmarPedido` |
| Abstração | O que a regra precisa, nas palavras dela | `RepositorioDePedidos`, `Notificador` |
| Baixo nível | O detalhe que implementa a abstração | `RepositorioMySQL`, `NotificadorSmtp` |
| Ponto de montagem | O único lugar que conhece as duas pontas | O `main` ou a configuração |

<a id="depois"></a>
## Como fica

```python
from typing import Protocol

# 1. as abstrações pertencem à regra, e usam o vocabulário dela
class RepositorioDePedidos(Protocol):
    def marcar_confirmado(self, pedido_id) -> None: ...

class Notificador(Protocol):
    def avisar(self, email, texto) -> None: ...

# 2. a regra recebe as dependências prontas, e não conhece nenhum detalhe
class ConfirmarPedido:
    def __init__(self, repositorio: RepositorioDePedidos, notificador: Notificador):
        self._repositorio = repositorio
        self._notificador = notificador

    def executar(self, pedido):
        self._repositorio.marcar_confirmado(pedido.id)
        self._notificador.avisar(pedido.email, "Confirmado")

# 3. os detalhes ficam de fora e apontam para as abstrações
class RepositorioMySQL:
    def marcar_confirmado(self, pedido_id): ...

# 4. o ponto de montagem: o único lugar que sabe quem é quem
caso_de_uso = ConfirmarPedido(RepositorioMySQL(), NotificadorSmtp())
```

> **Dica.** O teste de `ConfirmarPedido` passa duas classes de cinco linhas, que guardam o que receberam em uma lista, e confere a lista. Sem Docker, sem rede, sem relógio, e roda em milissegundos.

<a id="nao-confundir"></a>
## Três coisas com nome parecido

Na conversa do dia a dia, estes termos se misturam, e vale separá-los:

| Nome | O que é |
|---|---|
| Dependency **Inversion** | O princípio: a regra define a abstração e os detalhes a implementam. É uma decisão de *desenho* |
| Dependency **Injection** | A técnica: receber a dependência de fora (construtor, parâmetro), em vez de criá-la dentro. É o jeito mais comum de aplicar o princípio |
| **Container** de DI / IoC | Uma ferramenta que faz a montagem automaticamente. Opcional: o `main` escrito à mão resolve a maioria dos projetos |

É possível injetar sem inverter: se o construtor recebe `RepositorioMySQL` concreto, a dependência vem de fora, mas a seta continua apontando para o detalhe.

<a id="como-reconhecer"></a>
## Como reconhecer a violação

| Sintoma | O que está acontecendo |
|---|---|
| `import` de driver, SDK ou framework dentro do arquivo da regra | A regra conhece o detalhe pelo nome |
| `new` / construtor de classe concreta dentro de método de negócio | A regra decide qual detalhe usa, e não dá para trocar |
| `datetime.now()`, `random()`, `os.environ` no meio da regra | Até o relógio e o ambiente são dependências escondidas, e tornam o teste instável |
| Teste unitário que usa `patch("módulo.biblioteca")` para tudo | O teste precisa sabotar o código para escapar da dependência |
| Singleton ou variável global acessada de dentro da regra | Dependência escondida: a assinatura diz uma coisa, o corpo precisa de outra |

<a id="quando-nao-aplicar"></a>
## Quando não aplicar

Cada inversão custa uma interface e um ponto de montagem. Ela se paga nas dependências que **mudam, são lentas ou são difíceis de testar**. As estáveis não precisam.

| Situação | Por que não | Faça isto |
|---|---|---|
| Biblioteca padrão estável: `math`, `list`, `json` | Não muda e não tem efeito colateral; a abstração só adiciona ruído | Use direto |
| Script curto ou protótipo | O ponto de montagem seria maior que o próprio código | Escreva direto; inverta quando o primeiro teste doer |
| Classe de valor ou utilitário puro, sem I/O | Nada a trocar e nada a falsificar | Chame normalmente |

> **Perigo.** Sinal de exagero: uma interface para cada classe, nomeada `IAlgumaCoisa`, com uma única implementação e um nome que só repete o da classe. Se a abstração não representa uma decisão da regra, é só uma cópia da classe.

<a id="relacao"></a>
## Relação com os outros

O [Adapter](estruturais/adapter/explicacao.md) é o princípio aplicado quando a interface de fora não é a que a sua regra definiu: ele a traduz. O [Strategy](comportamentais/strategy/explicacao.md) usa a mesma inversão para o algoritmo, e as [fábricas](criacionais/factory-method/explicacao.md) resolvem o caso em que a regra precisa criar objetos sem conhecer a classe. E para que a abstração seja fácil de implementar, vale lembrar do [Interface Segregation](interface-segregation.md): pequena e feita para quem usa.
