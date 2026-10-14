<!-- Gerado de pages/clean-code/comportamentais/template-method/uso.html por scripts/sync_references.py. Não edite aqui: edite a página e rode o script. -->

# Template Method — Uso

*Clean Code / Design Pattern / Template Method*

Três situações em que o Template Method resolve o problema. Cada uma traz o código sem o pattern, o código com ele e o que a classe base passa a garantir.

<a id="como-escolhi"></a>
## Por que três

Cada exemplo entrou com uma regra: precisa trazer um **motivo diferente** para usar o Template Method. Quando dois casos se resolvem com o mesmo raciocínio — importar CSV e importar JSON, ou gerar relatório de vendas e de estoque — só um fica. Seguindo essa regra, sobraram três motivos. Os que ficaram de fora estão no [fim da página](#fora-da-lista).

| # | Situação | O que a classe base fixa |
|---|---|---|
| 1 | [Mesmo roteiro, um miolo diferente](#mesmo-roteiro) | A ordem dos passos |
| 2 | [Um passo que ninguém pode pular](#passo-obrigatorio) | O passo que não pode faltar |
| 3 | [Passos opcionais com padrão sensato](#ganchos-opcionais) | O comportamento de cada passo que ninguém trocou |

<a id="mesmo-roteiro"></a>
## 1. Mesmo roteiro, um miolo diferente

**Situação.** O financeiro recebe por e-mail um relatório de vendas do mês. A logística pediu o de estoque, e em seguida virão o de devoluções e o de comissões. Todos seguem a mesma sequência: buscar as linhas, calcular o total, gerar o CSV, enviar e registrar. Mudam a consulta, as colunas, a conta do total e o destinatário.

**sem o pattern — uma função por relatório, copiada da anterior**

```python
def relatorio_de_vendas(periodo):
    linhas = db.consultar("vendas", periodo)
    total = sum(l.valor for l in linhas)
    arquivo = csv_de(linhas, ["data", "produto", "valor"], rodape=total)
    email.enviar("financeiro@loja.com", arquivo)
    log.info("vendas: %d linhas", len(linhas))

def relatorio_de_estoque(periodo):
    linhas = db.consultar("estoque", periodo)
    total = sum(l.quantidade for l in linhas)
    arquivo = csv_de(linhas, ["sku", "deposito", "quantidade"], rodape=total)
    email.enviar("logistica@loja.com", arquivo)
    log.info("estoque: %d linhas", len(linhas))
```

**O que dói.** Cada relatório novo é copiar seis linhas e trocar quatro. A política muda de vez em quando (mandar cópia ao arquivo morto, trocar CSV por XLSX) e vira uma edição em todas as funções. E, quando alguém acrescenta um passo em uma delas, as outras ficam sem, sem nenhum aviso.

**com o pattern — o roteiro uma vez; cada relatório diz só o que é seu**

```python
class Relatorio(ABC):
    colunas: list[str]
    destinatario: str

    def gerar(self, periodo):                       # o roteiro
        linhas = self.buscar(periodo)
        arquivo = csv_de(linhas, self.colunas, rodape=self.totalizar(linhas))
        email.enviar(self.destinatario, arquivo)
        log.info("%s: %d linhas", type(self).__name__, len(linhas))

    @abstractmethod
    def buscar(self, periodo): ...

    @abstractmethod
    def totalizar(self, linhas): ...

class RelatorioDeVendas(Relatorio):
    colunas = ["data", "produto", "valor"]
    destinatario = "financeiro@loja.com"

    def buscar(self, periodo):
        return db.consultar("vendas", periodo)

    def totalizar(self, linhas):
        return sum(l.valor for l in linhas)

# RelatorioDeEstoque: a mesma forma, com outros quatro itens
RelatorioDeVendas().gerar(periodo)
```

**O que a classe base guarda.** A *ordem*: buscar, totalizar, gerar, enviar, registrar. Os pontos que variam ficam nomeados, e um relatório novo é uma classe pequena que só responde "de onde vêm as linhas e como se soma". Trocar CSV por XLSX, ou mandar cópia ao arquivo morto, é uma edição em `gerar` e vale para todos.

<a id="passo-obrigatorio"></a>
## 2. Um passo que ninguém pode pular

**Situação.** A loja recebe webhooks do gateway de pagamento, do correio e do marketplace. Para todos, o roteiro é o mesmo: conferir a assinatura (senão qualquer pessoa na internet marca pedidos como pagos), descartar eventos repetidos e só então tratar. O trabalho de tratar é de cada integração, escrita por pessoas diferentes ao longo do ano.

**sem o pattern — cada handler lembra (ou não) das proteções**

```python
def webhook_pagamento(request):
    if not assinatura_valida(request, SEGREDO_PAGAMENTO):
        return Resposta(401)
    evento = json.loads(request.body)
    if ja_processado(evento["id"]):
        return Resposta(200)
    marcar_pedido_pago(evento["pedido"])
    return Resposta(200)

def webhook_correio(request):
    evento = json.loads(request.body)       # e a assinatura? e o evento repetido?
    marcar_pedido_entregue(evento["pedido"])
    return Resposta(200)
```

**O que dói.** O handler do correio, escrito às pressas, esqueceu duas proteções, e ninguém notou porque ele "funciona". Uma pessoa de fora consegue marcar qualquer pedido como entregue. A auditoria de segurança precisa ler cada handler, um por um, para saber se está tudo lá.

**com o pattern — as proteções ficam no roteiro, e o handler só trata**

```python
class Webhook(ABC):
    segredo: str

    def receber(self, request):                      # o roteiro: ninguém pula passo
        if not assinatura_valida(request, self.segredo):
            return Resposta(401)
        evento = json.loads(request.body)
        if ja_processado(evento["id"]):
            return Resposta(200)
        self.tratar(evento)
        registrar_processado(evento["id"])
        return Resposta(200)

    @abstractmethod
    def tratar(self, evento): ...

class WebhookCorreio(Webhook):
    segredo = SEGREDO_CORREIO

    def tratar(self, evento):
        marcar_pedido_entregue(evento["pedido"])
```

**O que a classe base guarda.** O que *não pode faltar*. Quem escreve o handler nem chega a ver o código da assinatura: o que ele escreve é `tratar`, e a verificação acontece antes dele. A diferença para o exemplo 1 é o motivo: lá o pattern evita copiar; aqui ele torna impossível esquecer, e a auditoria passa a ler um método.

> **Cuidado.** Python não tem `final`: nada impede uma subclasse de redefinir `receber` e deixar a proteção de fora. Feche a brecha com um teste: `assert all("receber" not in vars(s) for s in Webhook.__subclasses__())`.

<a id="ganchos-opcionais"></a>
## 3. Passos opcionais com padrão sensato

**Situação.** Uma equipe mantém doze jobs agendados em Node: fechamento do dia, limpeza de sessões, reindexação. O roteiro é igual (decidir se roda, executar, tratar sucesso, tratar falha), mas cada job tem pequenas exceções: o fechamento pula fim de semana e avisa o financeiro; a limpeza avisa o plantão quando falha; o resto só quer um log.

**sem o pattern — cada job decide a própria política**

```typescript
async function jobFechamentoDoDia() {
  if (!ehDiaUtil()) return;                 // este pula fim de semana
  try {
    await fecharCaixa();
    await avisarFinanceiro("fechamento ok");
  } catch (e) {
    console.error(e);                       // este só loga
  }
}

async function jobLimpezaDeSessoes() {
  try {
    await apagarSessoesExpiradas();
  } catch (e) {
    await avisarPlantao(e);                // este avisa o plantão
    throw e;                                // e este relança
  }
}
```

**O que dói.** Cada job inventou a sua política de falha, e ninguém sabe qual é a regra da equipe. Registrar a duração de todos os jobs, ou impedir que um job falhe em silêncio, é uma edição em doze funções. E um job novo começa copiando "o último que funcionou", com as exceções dele.

**com o pattern — um passo obrigatório e três ganchos com padrão**

```typescript
abstract class Job {
  async rodar() {                                       // o roteiro
    if (!this.deveRodar()) return;
    const inicio = Date.now();
    try {
      await this.executar();
      await this.aoSucesso();
    } catch (erro) {
      await this.aoFalhar(erro as Error);
    } finally {
      console.log(`${this.constructor.name}: ${Date.now() - inicio}ms`);
    }
  }

  protected abstract executar(): Promise<void>;       // obrigatório

  protected deveRodar(): boolean { return true; }          // ganchos: têm padrão
  protected async aoSucesso(): Promise<void> {}
  protected async aoFalhar(erro: Error): Promise<void> { console.error(erro); }
}

class FechamentoDoDia extends Job {
  protected deveRodar() { return ehDiaUtil(); }
  protected async executar() { await fecharCaixa(); }
  protected async aoSucesso() { await avisarFinanceiro("fechamento ok"); }
}

class LimpezaDeSessoes extends Job {
  protected async executar() { await apagarSessoesExpiradas(); }
  protected async aoFalhar(erro: Error) { await avisarPlantao(erro); }
}
```

**O que a classe base guarda.** O *padrão de cada passo*. O código separa o que é obrigatório (`executar`, abstrato: o compilador cobra) do que é opcional (os ganchos, com um comportamento sensato que só quem precisa troca). Um job comum escreve uma linha. A política da equipe (medir duração, por exemplo) vive em `rodar` e chega a todos.

> **Cuidado.** Cada gancho é uma promessa de que o pai chamará aquele método naquele ponto, para sempre. Comece com os que dois jobs já precisaram. Doze ganchos "por precaução" viram uma classe base que ninguém consegue ler.

<a id="fora-da-lista"></a>
## O que ficou de fora

Casos comuns que não ganharam seção própria, porque o motivo já está em um dos três:

| Caso | Já coberto por |
|---|---|
| Importar CSV, JSON e XML com o mesmo fluxo | 1 — veja a [Explicação](explicacao.md#o-problema) |
| Gerar o mesmo recibo em PDF e em HTML | 1 — o roteiro é igual; muda a renderização |
| Jogo de turnos com regras diferentes (iniciar, jogar turno, ver se acabou) | 1 — a ordem é fixa, e os passos mudam |
| Autenticar, autorizar, validar e só então executar uma ação | 2 — os primeiros passos não podem faltar |
| `setUp` e `tearDown` de uma classe de testes | 3 — ganchos com padrão vazio; e 2, porque o `tearDown` sempre roda |
| Métodos de ciclo de vida de um componente (`aoMontar`, `aoDestruir`) | 3 — o framework é dono do roteiro e você preenche ganchos |
| Abrir e fechar um recurso em volta de um trecho | 2 — mas um `with` costuma bastar (veja [Quando não usar](explicacao.md#quando-nao-usar)) |

E um caso que parece Template Method, mas não é: `sorted(itens, key=preco)`. O roteiro é da biblioteca e você preenche um passo, mas o passo vai como *função*, sem herança, e pode ser trocado a cada chamada. Isso é Strategy, ou um callback simples. Veja também [Parecidos](explicacao.md#parecidos).
