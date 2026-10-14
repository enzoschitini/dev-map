<!-- Gerado de pages/clean-code/estruturais/bridge/uso.html por scripts/sync_references.py. Não edite aqui: edite a página e rode o script. -->

# Bridge — Uso

*Clean Code / Design Pattern / Bridge*

Três situações em que o Bridge resolve o problema. Cada uma traz o código sem o pattern, o código com ele e o que a ponte mantém separado em cada caso.

<a id="como-escolhi"></a>
## Por que três

Cada exemplo entrou com uma regra: precisa trazer um **motivo diferente** para usar o Bridge. Quando dois casos se resolvem com o mesmo raciocínio — tema escuro contra componentes de UI e fila de tarefas contra broker, por exemplo, são os mesmos dois eixos do primeiro exemplo — só um fica. O Bridge tem poucos motivos genuínos, e vários casos que parecem Bridge são outra coisa. Sobraram três. Os que ficaram de fora estão no [fim da página](#fora-da-lista).

| # | Situação | O que a ponte separa |
|---|---|---|
| 1 | [Avisos e canais que crescem juntos](#avisos-e-canais) | O conteúdo do aviso do transporte que o entrega |
| 2 | [O mesmo gráfico no navegador e no servidor](#mesmo-grafico-varios-ambientes) | O que desenhar do lugar onde se desenha |
| 3 | [Vários bancos na mesma biblioteca de consultas](#bancos-de-dados) | A lógica de alto nível das primitivas de cada banco |

> **Nota.** O gateway de SMS do primeiro exemplo é fictício. O e-mail usa a biblioteca padrão e o Slack usa o formato real do webhook de entrada, simplificado.

<a id="avisos-e-canais"></a>
## 1. Avisos e canais que crescem juntos

**Situação.** A loja avisa o cliente sobre a confirmação do pedido e sobre cobrança atrasada, por e-mail e por SMS. Chegou o Slack para o time interno, e vem um aviso de estoque baixo. O que cada aviso diz e por onde ele sai são decisões de pessoas diferentes: o comercial muda o texto; a infraestrutura troca o provedor.

**sem o pattern — uma classe para cada par aviso × canal**

```python
class ConfirmacaoPorEmail:
    def enviar(self, pedido):
        msg = EmailMessage()
        msg["To"] = pedido.email
        msg["Subject"] = f"Pedido {pedido.id} confirmado"
        msg.set_content(f"Total: R$ {pedido.total:.2f}")
        with smtplib.SMTP(SMTP_HOST) as s:
            s.send_message(msg)

class ConfirmacaoPorSms:
    def enviar(self, pedido):
        texto = f"Pedido {pedido.id} confirmado. Total: R$ {pedido.total:.2f}"
        sms_gateway.enviar(pedido.telefone, texto[:160])

class CobrancaAtrasadaPorEmail:
    def enviar(self, fatura):
        msg = EmailMessage()      # o mesmo SMTP, de novo
        ...

class CobrancaAtrasadaPorSms:
    def enviar(self, fatura):
        texto = f"Fatura {fatura.id} vencida. Valor: R$ {fatura.valor:.2f}"
        sms_gateway.enviar(fatura.telefone, texto[:140])  # 140? em outras é 160

# ConfirmacaoPorSlack, CobrancaAtrasadaPorSlack,
# EstoqueBaixoPorEmail, EstoqueBaixoPorSms, EstoqueBaixoPorSlack...
```

**O que dói.** Três avisos e três canais são nove classes, e a décima não custa uma: um canal novo (WhatsApp) é uma classe em cada aviso, e um aviso novo é uma em cada canal. O código do canal está copiado — e já divergiu, com o corte do SMS em 160 num lugar e 140 em outro. Mudar a redação de "Pedido confirmado" é abrir três arquivos.

**com o pattern — o aviso produz o texto, o canal o entrega**

```python
# a implementação: o canal escolhe qual contato usar e como entregar
class Canal(Protocol):
    def entregar(self, dest: Destinatario, assunto: str, corpo: str) -> None: ...

class CanalEmail:
    def entregar(self, dest, assunto, corpo):
        msg = EmailMessage()
        msg["To"], msg["Subject"] = dest.email, assunto
        msg.set_content(corpo)
        with smtplib.SMTP(SMTP_HOST) as s:
            s.send_message(msg)

class CanalSms:
    LIMITE = 160   # uma regra do SMS, em um lugar só

    def entregar(self, dest, assunto, corpo):
        sms_gateway.enviar(dest.telefone, f"{assunto}: {corpo}"[:self.LIMITE])

class CanalSlack:
    def entregar(self, dest, assunto, corpo):
        requests.post(dest.slack_webhook, json={"text": f"*{assunto}*\n{corpo}"})

# a abstração: o conteúdo, sem saber como sai
class Aviso(ABC):
    def __init__(self, canal: Canal):
        self._canal = canal

    @abstractmethod
    def assunto(self) -> str: ...
    @abstractmethod
    def corpo(self) -> str: ...

    def enviar(self, dest: Destinatario):
        self._canal.entregar(dest, self.assunto(), self.corpo())

class ConfirmacaoDePedido(Aviso):
    def __init__(self, canal, pedido):
        super().__init__(canal)
        self._pedido = pedido

    def assunto(self):
        return f"Pedido {self._pedido.id} confirmado"

    def corpo(self):
        return f"Total: R$ {self._pedido.total:.2f}"

# qualquer aviso com qualquer canal
ConfirmacaoDePedido(CanalSms(), pedido).enviar(cliente)
```

**O que a ponte separa.** O texto e o transporte. Três avisos e três canais são **6** classes, não 9, e o WhatsApp vira uma classe que todos os avisos já sabem usar. O limite de 160 caracteres mora em `CanalSms`, que é onde ele pertence: o aviso nunca soube que SMS tem limite. O canal também decide qual campo do destinatário usar (`email`, `telefone`), então o aviso não carrega endereços.

> **Cuidado.** Mantenha o conteúdo neutro. Quando o aviso começa a produzir "negrito para o Slack" e "HTML para o e-mail", o canal vazou para dentro da abstração e você voltou ao ponto de partida. Entregue texto simples e deixe o canal enriquecer.

<a id="mesmo-grafico-varios-ambientes"></a>
## 2. O mesmo gráfico no navegador e no servidor

**Situação.** O painel web desenha gráficos em um `<canvas>`. O relatório semanal por e-mail precisa dos mesmos gráficos, gerados no servidor, onde não existe DOM. E-mail não executa script, então o servidor vai devolver SVG. O desenho precisa ser o mesmo nos dois lugares.

**sem o pattern — cada gráfico desenha duas vezes**

```typescript
class GraficoDeBarras {
  constructor(private dados: number[]) {}

  desenhar(canvas?: HTMLCanvasElement): string | void {
    if (canvas) {
      const ctx = canvas.getContext("2d")!;
      this.dados.forEach((v, i) => {
        ctx.fillStyle = "#2563eb";
        ctx.fillRect(i * 48, 200 - v, 40, v);
      });
    } else {
      // servidor: o mesmo layout, escrito à mão em SVG
      const barras = this.dados.map((v, i) =>
        `<rect x="${i * 48}" y="${200 - v}" width="40" height="${v}" fill="#2563eb"/>`);
      return `<svg width="400" height="200">${barras.join("")}</svg>`;
    }
  }
}

// GraficoDeLinha: o mesmo if/else. GraficoDePizza: idem.
```

**O que dói.** O layout (posição, largura, espaçamento) está escrito duas vezes por gráfico, e as duas cópias divergem na primeira semana: a barra do painel fica 4 pixels mais larga que a do e-mail. O tipo `HTMLCanvasElement` aparece em código que também roda no Node. E um terceiro destino (PDF, PNG) é mais um `else` em cada gráfico.

**com o pattern — o gráfico desenha em uma superfície abstrata**

```typescript
// a implementação: três primitivas de desenho
interface Superficie {
  retangulo(x: number, y: number, larg: number, alt: number, cor: string): void;
  linha(x1: number, y1: number, x2: number, y2: number, cor: string): void;
  texto(x: number, y: number, conteudo: string): void;
}

class SuperficieCanvas implements Superficie {
  constructor(private ctx: CanvasRenderingContext2D) {}

  retangulo(x, y, larg, alt, cor) {
    this.ctx.fillStyle = cor;
    this.ctx.fillRect(x, y, larg, alt);
  }
  linha(x1, y1, x2, y2, cor) {
    this.ctx.strokeStyle = cor;
    this.ctx.beginPath();
    this.ctx.moveTo(x1, y1);
    this.ctx.lineTo(x2, y2);
    this.ctx.stroke();
  }
  texto(x, y, conteudo) { this.ctx.fillText(conteudo, x, y); }
}

class SuperficieSvg implements Superficie {
  private partes: string[] = [];

  retangulo(x, y, larg, alt, cor) {
    this.partes.push(`<rect x="${x}" y="${y}" width="${larg}" height="${alt}" fill="${cor}"/>`);
  }
  linha(x1, y1, x2, y2, cor) {
    this.partes.push(`<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" stroke="${cor}"/>`);
  }
  texto(x, y, conteudo) {
    this.partes.push(`<text x="${x}" y="${y}">${conteudo}</text>`);
  }
  resultado() { return `<svg width="400" height="200">${this.partes.join("")}</svg>`; }
}

// a abstração: o gráfico, sem saber onde desenha
abstract class Grafico {
  constructor(protected superficie: Superficie, protected dados: number[]) {}
  abstract desenhar(): void;
}

class GraficoDeBarras extends Grafico {
  desenhar() {
    this.dados.forEach((v, i) => this.superficie.retangulo(i * 48, 200 - v, 40, v, "#2563eb"));
  }
}

// painel (navegador)
new GraficoDeBarras(new SuperficieCanvas(ctx), dados).desenhar();

// relatório por e-mail (servidor)
const svg = new SuperficieSvg();
new GraficoDeBarras(svg, dados).desenhar();
return svg.resultado();
```

**O que a ponte separa.** O que desenhar do lugar onde se desenha. O layout existe uma vez, em `GraficoDeBarras`, e por isso o painel e o e-mail *não podem* divergir. Quem escolhe a superfície é a montagem, em cada ambiente: nenhum gráfico testa `typeof document`. O que muda em relação ao exemplo anterior é o **momento** da decisão: o gráfico é escolhido pelo código, mas a superfície é escolhida pelo ambiente em que ele roda.

A interface de implementação tem três métodos de propósito. Uma superfície nova (PNG, PDF, terminal) implementa três coisas, e todos os gráficos passam a funcionar nela.

> **Dica.** O teste vira trivial: uma `SuperficieEspia` guarda as chamadas, e `expect(espia.retangulos).toHaveLength(3)` confere o gráfico sem navegador, sem DOM e sem imagem.

<a id="bancos-de-dados"></a>
## 3. Vários bancos na mesma biblioteca de consultas

**Situação.** A biblioteca interna de relatórios monta consultas por uma API encadeada: `Consulta("pedidos").onde("status", "pago").limite(10)`. Ela nasceu no Postgres. Agora o time de dados quer rodar os testes no SQLite, e um cliente exige SQL Server. A biblioteca é usada por outros times, que vão querer o próprio banco.

**sem o pattern — um if por banco em cada método**

```python
class Consulta:
    def __init__(self, tabela, banco="postgres"):
        self._tabela, self._banco = tabela, banco
        self._filtros, self._limite = [], None

    def montar(self):
        if self._banco == "postgres":
            nome = f'"{self._tabela}"'
        elif self._banco == "sqlserver":
            nome = f"[{self._tabela}]"
        else:
            nome = self._tabela

        sql = f"SELECT * FROM {nome}"
        if self._filtros:
            marcador = "%s" if self._banco == "postgres" else "?"
            # ...e as aspas dos nomes das colunas, repetidas aqui
            sql += " WHERE " + " AND ".join(f"{c} = {marcador}" for c, _ in self._filtros)

        if self._limite:
            if self._banco == "sqlserver":
                sql = sql.replace("SELECT", f"SELECT TOP {self._limite}", 1)
            else:
                sql += f" LIMIT {self._limite}"
        return sql, [v for _, v in self._filtros]
```

**O que dói.** Cada recurso novo (`ordenar_por`, `juntar`) exige um `if` por banco, e o método cresce na vertical. O quarto banco só entra editando a classe central, que é de outro time. E a lógica de "montar uma consulta" está embaralhada com a de "como este banco escreve isso", então ninguém sabe se uma mudança é segura.

**com o pattern — o dialeto só sabe três coisas**

```python
# a implementação: só o que muda de banco para banco
class Dialeto(Protocol):
    def identificador(self, nome: str) -> str: ...
    def marcador(self) -> str: ...
    def limitar(self, sql: str, n: int) -> str: ...

class Postgres:
    def identificador(self, nome):
        return '"' + nome.replace('"', '""') + '"'
    def marcador(self):
        return "%s"
    def limitar(self, sql, n):
        return f"{sql} LIMIT {n}"

class Sqlite:
    def identificador(self, nome):
        return '"' + nome.replace('"', '""') + '"'
    def marcador(self):
        return "?"
    def limitar(self, sql, n):
        return f"{sql} LIMIT {n}"

class SqlServer:
    def identificador(self, nome):
        return "[" + nome.replace("]", "]]") + "]"
    def marcador(self):
        return "?"
    def limitar(self, sql, n):
        return sql.replace("SELECT", f"SELECT TOP {n}", 1)

# a abstração: monta a consulta, sem conhecer nenhum banco pelo nome
class Consulta:
    def __init__(self, tabela: str, dialeto: Dialeto):
        self._tabela, self._dialeto = tabela, dialeto
        self._filtros, self._limite = [], None

    def onde(self, coluna, valor):
        self._filtros.append((coluna, valor))
        return self

    def limite(self, n):
        self._limite = n
        return self

    def montar(self):
        d = self._dialeto
        sql = f"SELECT * FROM {d.identificador(self._tabela)}"
        if self._filtros:
            condicoes = " AND ".join(
                f"{d.identificador(c)} = {d.marcador()}" for c, _ in self._filtros
            )
            sql += f" WHERE {condicoes}"
        if self._limite is not None:
            sql = d.limitar(sql, self._limite)
        return sql, [v for _, v in self._filtros]

Consulta("pedidos", SqlServer()).onde("status", "pago").limite(10).montar()
```

**O que a ponte separa.** A lógica de alto nível das primitivas de cada banco. Este exemplo ensina o que os outros dois não ensinam: a interface de implementação é feita de **operações pequenas** (`identificador`, `marcador`, `limitar`), e a composição fica toda na abstração. Por isso um banco novo é um punhado de métodos, escrito por quem quiser, sem tocar em `Consulta`. A mesma separação aparece no SQLAlchemy, que constrói a consulta em Python e delega a um dialeto a escrita do SQL para cada banco.

O outro lado também rende: `Consulta` pode ganhar refinações (paginação, agregação) sem que nenhum dialeto precise saber, desde que elas só usem as primitivas que já existem.

> **Cuidado.** Cada primitiva nova é um custo para todos os dialetos, inclusive os escritos por outros times. Acrescente uma só quando dois bancos *realmente* divergem naquele ponto, e não por conforto da abstração.

<a id="fora-da-lista"></a>
## O que ficou de fora

Casos comuns que não ganharam seção própria, porque o motivo já está em um dos três:

| Caso | Já coberto por |
|---|---|
| Tema (claro, escuro, alto contraste) contra componentes de UI | 1 — dois eixos que se combinam |
| Fila de tarefas (imediata, agendada) contra broker (Redis, SQS) | 1 — dois eixos que se combinam |
| Tipos de etiqueta contra modelos de impressora | 1 — e, se a impressora é uma linguagem de comandos, 3 — primitivas |
| Renderizar o mesmo documento na web e no app nativo | 2 — o ambiente escolhe a implementação |
| Drivers de dispositivo, de banco ou de impressora | 3 — implementações escritas por outras pessoas, sobre primitivas |

E dois casos que parecem Bridge, mas não são. O primeiro: uma interface com duas implementações escolhidas por configuração, como o `Armazenamento` local e S3 do [exemplo 4 do Adapter](../adapter/uso.md#dependencia-de-infra). Só um lado varia, e a "abstração" não tem variantes próprias: é injeção de dependência, e o nome do pattern aqui só complica. O segundo: um cliente que alterna entre WebSocket e *polling* quando a conexão falha. A implementação troca durante a vida do objeto, e isso é Strategy (ou State). Veja a seção [Parecidos](explicacao.md#parecidos) da explicação.
