<!-- Gerado de pages/clean-code/criacionais/builder/explicacao.html por scripts/sync_references.py. Não edite aqui: edite a página e rode o script. -->

# Builder — Explicação

*Clean Code / Design Pattern / Builder*

Como montar um objeto complexo por partes, em etapas, e só entregá-lo quando estiver completo e válido — em vez de deixá-lo circulando pela metade.

<a id="o-problema"></a>
## O problema

O sistema envia um e-mail de confirmação a cada pedido. Quem monta esse e-mail não é um lugar só: o destinatário vem do cadastro, a assinatura vem de um módulo de marca, o PDF da nota fiscal vem do módulo fiscal. Cada parte acrescenta o que sabe.

A saída mais curta é criar o objeto vazio e passá-lo de função em função, para cada uma preencher a sua parte:

**antes — o objeto existe pela metade durante toda a montagem**

```python
class Email:
    def __init__(self):
        self.para = []
        self.assunto = ""
        self.corpo = ""
        self.anexos = []

def email_de_confirmacao(pedido):
    email = Email()
    email.para = [pedido.cliente.email]
    adicionar_assinatura(email)              # corpo = "\n--\nLoja X"
    email.corpo = f"Seu pedido {pedido.id} foi confirmado."   # apagou a assinatura
    anexar_nota_fiscal(email, pedido)
    return email

enviar(email_de_confirmacao(pedido))   # sem assunto — e ninguém conferiu
```

Três coisas quebram. O objeto é **inválido** do começo ao fim — no meio do caminho ele não tem assunto, e nada o impede de ser enviado assim. A **ordem** das chamadas importa, mas nada a documenta: aqui, a atribuição ao `corpo` apagou a assinatura. E, como o objeto é mutável, qualquer um com a referência pode alterá-lo depois de "pronto".

<a id="a-solucao"></a>
## A solução

Separe **montar** de **ter**. Um objeto auxiliar, o builder, recebe as partes em qualquer ordem e as guarda; o produto só nasce quando alguém pede, e nesse momento o conjunto é validado. São cinco papéis:

| Papel | Quem é | No exemplo |
|---|---|---|
| Produto | O objeto final, completo e imutável | `Email` |
| Builder | Guarda as partes enquanto a montagem acontece | `EmailBuilder` |
| Etapas | Os métodos que acrescentam uma parte e devolvem o próprio builder | `para()`, `assunto()`, `corpo()`, `anexar()` |
| Montagem final | O passo que valida o conjunto e entrega o produto | `construir()` |
| Cliente | Quem monta, sem tocar no produto até ele estar pronto | `email_de_confirmacao()` |

O ponto é **quando o objeto passa a existir**. Antes, ele existia desde a primeira linha e ficava inválido por um tempo. Agora ele só existe depois de `construir()`, e a validação mora nesse único momento: ou volta um `Email` completo, ou volta um erro dizendo o que faltou.

<a id="implementacao"></a>
## Implementação

```python
from dataclasses import dataclass

# 1. o produto: completo, imutável, sem setters
@dataclass(frozen=True)
class Email:
    para: tuple[str, ...]
    assunto: str
    corpo: str
    anexos: tuple[str, ...] = ()

# 2. o builder: guarda as partes, em qualquer ordem
class EmailBuilder:
    def __init__(self):
        self._para = []
        self._assunto = None
        self._partes_do_corpo = []
        self._anexos = []

    # 3. as etapas: cada uma acrescenta e devolve self
    def para(self, endereco: str):
        self._para.append(endereco)
        return self

    def assunto(self, texto: str):
        self._assunto = texto
        return self

    def corpo(self, texto: str):
        self._partes_do_corpo.append(texto)   # acumula: a assinatura não apaga nada
        return self

    def anexar(self, caminho: str):
        self._anexos.append(caminho)
        return self

    # 4. a montagem final: valida o conjunto e entrega o produto
    def construir(self) -> Email:
        if not self._para:
            raise ValueError("e-mail sem destinatário")
        if not self._assunto:
            raise ValueError("e-mail sem assunto")
        return Email(
            para=tuple(self._para),
            assunto=self._assunto,
            corpo="\n".join(self._partes_do_corpo),
            anexos=tuple(self._anexos),
        )

# 5. o cliente: monta, e só então tem um Email
def email_de_confirmacao(pedido):
    return (EmailBuilder()
        .para(pedido.cliente.email)
        .assunto(f"Pedido {pedido.id}")
        .corpo(f"Seu pedido {pedido.id} foi confirmado.")
        .anexar(nota_fiscal_em_pdf(pedido))
        .corpo(ASSINATURA)
        .construir())
```

> **Dica.** O erro de montagem agora aparece em `construir()`, no ponto onde o e-mail foi montado, e diz o que faltou. Antes, ele aparecia em `enviar()`, mais longe do erro e talvez com o cliente já esperando o e-mail.

> **Nota.** Em Python, quando todos os campos são conhecidos de uma vez, `Email(para=(...), assunto="...", corpo="...")` com o dataclass já basta. O Builder se paga quando a montagem é *em etapas*, *por pontos diferentes do código* ou com *validação do conjunto*.

<a id="quando-usar"></a>
## Quando usar

O Builder vale quando as três coisas acontecem ao mesmo tempo: o objeto é **montado em etapas** (em mais de um lugar, ou acumulando partes), só é válido **completo**, e você quer que ele **nasça pronto** — imutável, ou com o mesmo roteiro gerando saídas diferentes.

No código, isso aparece de formas reconhecíveis:

| Situação | Como reconhecer no código | Exemplo |
|---|---|---|
| Um objeto passa por várias funções que o preenchem | `adicionar_x(obj)`, `anexar_y(obj)`, `aplicar_z(obj)` em sequência, antes de alguém usá-lo | — |
| Validação espalhada por quem usa | `if not obj.assunto` repetido em cada função que recebe o objeto | — |
| O mesmo roteiro com saídas diferentes | `if formato == "html"` dentro de cada passo da geração | [Uso #1](uso.md#mesmo-roteiro) |
| Duas coleções mantidas em sincronia | `sql += …` junto de `params.append(…)`, em todo ramo | [Uso #2](uso.md#estado-interno) |
| Montar o objeto no teste dá mais trabalho que o teste | Dez linhas de construção para afirmar sobre um único campo | [Uso #3](uso.md#dados-de-teste) |

> **Dica.** O que os sinais têm em comum: a pergunta nunca é "tenho muitos parâmetros?". É "**existe um momento em que o objeto está incompleto**, e alguém pode ver ou usar esse estado?".

<a id="teste-rapido"></a>
### Um teste rápido

Na dúvida, responda em ordem. A primeira resposta que manda parar decide.

1. **O objeto tem poucos campos, todos conhecidos de uma vez?** Use o construtor, com argumentos nomeados.
2. **O problema é só "muitos parâmetros opcionais"?** Argumentos nomeados, um dataclass ou um objeto de opções resolvem sem uma classe nova.
3. **Existe montagem em etapas, validação do conjunto, ou mais de uma saída?** Se nenhuma das três, não é caso de Builder.
4. **Alguém pode usar o objeto antes de ele estar pronto?** Se sim, é exatamente o que o Builder resolve.

<a id="quando-nao-usar"></a>
## Quando não usar

O Builder paga com **uma classe a mais por produto**, que quase espelha os campos dele: cada campo novo muda duas classes, e a cadeia de chamadas parece um fluxo simples mas guarda estado escondido. Para um objeto de três campos, o custo não se paga em lugar nenhum.

| Situação | Por que não | Faça isto |
|---|---|---|
| O objeto tem poucos campos e todos conhecidos de uma vez | O builder só repete os campos em outra classe | Construtor, ou um dataclass |
| Muitos parâmetros opcionais e mais nada | Argumentos nomeados já deixam a chamada legível | `Cliente(timeout=5, retries=3)`; em TypeScript, um objeto de opções |
| Você quer "o mesmo objeto, com um campo diferente" | Criar um builder para isso é desproporcional | `dataclasses.replace(obj, assunto="…")` ou o spread `{ ...obj, assunto }` |
| O problema é qual *classe* criar | O Builder decide como montar, não o que montar | Factory Method, ou uma função fábrica |
| Vários objetos que precisam combinar entre si | Um builder monta um objeto; a consistência entre vários fica de fora | Abstract Factory |

<a id="sinais-de-abuso"></a>
### Sinais de que o Builder saiu do lugar

- **O builder espelha o produto campo a campo.** Se cada método só guarda um valor e `construir()` só repassa, é um construtor com mais arquivos.
- **`construir()` nunca falha.** Sem validação e sem decisão, o momento "pronto" não significa nada.
- **O builder é reutilizado depois de construir.** Se a lista interna é entregue ao produto sem cópia, o próximo produto herda as partes do anterior, ou o primeiro muda sozinho.
- **O produto também tem setters.** Se dá para alterá-lo depois, a garantia de "nasce pronto" não vale nada.
- **Um builder com 30 métodos.** O produto é grande demais: o problema é que ele está fazendo coisa demais, e a solução é dividi-lo.

> **Perigo.** O sinal mais comum: `construir()` só repassa o que recebeu. O padrão virou uma sintaxe diferente para o mesmo construtor.

> **Nota.** Na dúvida, comece com o construtor e argumentos nomeados. O momento do Builder chega com a primeira validação que depende de *vários campos juntos*, ou a primeira montagem espalhada por mais de uma função. Nesses dois casos a migração é pequena.

<a id="parecidos"></a>
## Parecidos

| Padrão | Diferença |
|---|---|
| [Abstract Factory](../abstract-factory/explicacao.md) | Entrega *vários* objetos de uma família, cada um em uma chamada. O Builder monta *um* objeto complexo, em etapas |
| [Factory Method](../factory-method/explicacao.md) | Decide *qual classe* criar. O Builder decide *como montar* o objeto |
| Argumentos nomeados / dataclass | Resolvem a legibilidade no ponto da chamada. O Builder acrescenta etapas, acúmulo de partes e validação final |
| Interface fluente (encadeamento) | É só a sintaxe de `a().b().c()`. O Builder costuma usá-la, mas `lista.filter().map()` é encadeamento sem Builder: não há montagem nem produto |

Regra prática: se a dificuldade é o objeto ser *montado* de forma complicada, é Builder. Se é decidir *qual tipo* de objeto criar, é uma fábrica.
