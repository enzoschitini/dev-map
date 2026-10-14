<!-- Gerado de pages/clean-code/comportamentais/command/uso.html por scripts/sync_references.py. Não edite aqui: edite a página e rode o script. -->

# Command — Uso

*Clean Code / Design Pattern / Command*

Quatro situações em que o Command resolve o problema. Cada uma traz o código sem o pattern, o código com ele e o que o comando carrega além de "executar".

<a id="como-escolhi"></a>
## Por que quatro

Cada exemplo entrou com uma regra: precisa trazer um **motivo diferente** para usar o Command. Quando dois casos se resolvem com o mesmo raciocínio — o histórico de auditoria e a fila de tarefas, por exemplo — só um fica. Seguindo essa regra, sobraram quatro motivos. Os que ficaram de fora estão no [fim da página](#fora-da-lista).

| # | Situação | O que o comando carrega |
|---|---|---|
| 1 | [Desfazer e refazer em um editor](#desfazer-refazer) | O valor antigo: o mínimo para voltar |
| 2 | [Trabalho que roda depois, em outro processo](#fila-de-tarefas) | Os dados do pedido, sem nenhum objeto vivo |
| 3 | [A mesma ação em botão, menu e atalho](#varios-gatilhos) | Nome, atalho e se está habilitada |
| 4 | [Passos que valem por inteiro ou nada](#lote-tudo-ou-nada) | Os passos e a ordem para desfazê-los |

<a id="desfazer-refazer"></a>
## 1. Desfazer e refazer em um editor

**Situação.** Um editor de planilhas. Quem edita usa Ctrl+Z e Ctrl+Y o tempo todo, em planilhas de cem mil células. A Explicação mostrou o desfazer simples; aqui entram o *refazer* e a restrição de memória.

**sem o pattern — uma cópia da planilha a cada edição**

```python
class Editor:
    def __init__(self, planilha):
        self.planilha = planilha
        self._passado, self._futuro = [], []

    def editar_celula(self, ref, valor):
        self._passado.append(copy.deepcopy(self.planilha))   # 100 mil células, a cada tecla
        self._futuro.clear()
        self.planilha[ref] = valor

    def desfazer(self):
        if self._passado:
            self._futuro.append(self.planilha)
            self.planilha = self._passado.pop()          # troca o objeto inteiro
```

**O que dói.** A memória cresce com o tamanho da planilha multiplicado pelo número de edições, para guardar a mudança de uma célula. O desfazer troca o objeto inteiro, então o gráfico e a seleção, que seguravam a planilha antiga, ficam apontando para a versão errada. E o menu não consegue dizer "Desfazer: editar B4", porque a cópia não sabe o que mudou.

**com o pattern — o comando guarda só a célula e o valor antigo**

```python
class EditarCelula(Comando):
    def __init__(self, planilha, ref, novo):
        self._planilha, self._ref, self._novo = planilha, ref, novo
        self._antigo = None

    def executar(self):
        self._antigo = self._planilha[self._ref]   # captura na hora de executar
        self._planilha[self._ref] = self._novo

    def desfazer(self):
        self._planilha[self._ref] = self._antigo

    @property
    def nome(self):
        return f"editar {self._ref}"

class Historico:
    def __init__(self):
        self._passado, self._futuro = [], []

    def executar(self, comando):
        comando.executar()
        self._passado.append(comando)
        self._futuro.clear()                 # uma ação nova invalida o "refazer"

    def desfazer(self):
        if self._passado:
            comando = self._passado.pop()
            comando.desfazer()
            self._futuro.append(comando)

    def refazer(self):
        if self._futuro:
            comando = self._futuro.pop()
            comando.executar()
            self._passado.append(comando)
```

**O que o comando carrega.** O menor pedaço de estado que basta para voltar: uma referência e um valor, e não a planilha inteira. A mudança de uma célula custa o que uma célula custa. Refazer é executar o mesmo objeto de novo, sem reconstruir nada, e o `nome` alimenta o texto do menu.

> **Cuidado.** O valor antigo é capturado em `executar`, não no construtor. Se dois comandos para a mesma célula forem criados antes de qualquer um rodar, o segundo guardaria um "antigo" que já não é o antigo na hora em que ele executa.

<a id="fila-de-tarefas"></a>
## 2. Trabalho que roda depois, em outro processo

**Situação.** Ao fechar um pedido, o sistema envia o e-mail de confirmação, emite a nota fiscal e baixa o estoque. Hoje tudo isso acontece dentro da requisição. O objetivo é responder ao cliente na hora e deixar o resto para um worker, com nova tentativa quando um serviço estiver fora.

**sem o pattern — tudo dentro da requisição**

```python
def fechar_pedido(pedido):
    pedido.confirmar()
    enviar_email(pedido.cliente.email, f"Pedido {pedido.id} confirmado")   # 1,5 s; se cair, o pedido falha
    emitir_nota_fiscal(pedido)                                            # 3 s
    estoque.baixar(pedido.itens)

# a "melhoria" mais comum: jogar em uma Thread com os argumentos soltos.
# se o servidor reiniciar agora, o e-mail e a nota nunca saem.
threading.Thread(target=enviar_email, args=(pedido.cliente.email, f"Pedido {pedido.id} confirmado")).start()
```

**O que dói.** O cliente espera cinco segundos, e uma falha no servidor de e-mail derruba um pedido que já foi pago. A thread resolve a espera, mas a tarefa existe só na memória daquele processo: uma reinicialização a apaga, e não há como tentar de novo, porque a "tarefa" é uma chamada que já saiu.

**com o pattern — o pedido vira um dado que atravessa a fila**

```python
@dataclass
class EnviarEmailDeConfirmacao:
    pedido_id: int                       # o id, não o objeto Pedido

    def executar(self, servicos):
        pedido = servicos.pedidos.obter(self.pedido_id)
        servicos.email.enviar(pedido.cliente.email, f"Pedido {pedido.id} confirmado")

# EmitirNotaFiscal e BaixarEstoque seguem o mesmo formato
COMANDOS = {c.__name__: c for c in (EnviarEmailDeConfirmacao, EmitirNotaFiscal, BaixarEstoque)}

def publicar(comando):
    fila.publicar({"tipo": type(comando).__name__, "dados": asdict(comando)})

def fechar_pedido(pedido):
    pedido.confirmar()
    for comando in (EnviarEmailDeConfirmacao(pedido.id), EmitirNotaFiscal(pedido.id), BaixarEstoque(pedido.id)):
        publicar(comando)

# em outro processo
def worker(servicos):
    for msg in fila.consumir():
        comando = COMANDOS[msg["tipo"]](**msg["dados"])
        try:
            comando.executar(servicos)
        except ErroTemporario:
            fila.devolver(msg)             # tentar de novo é reenfileirar
```

**O que o comando carrega.** Dados, e só dados: um id e o nome da classe. Por isso ele cabe em JSON, atravessa processos, sobrevive a uma reinicialização e pode ser reenviado. Quem fecha o pedido não espera e não sabe quem executará; o worker não sabe de onde o comando veio. Aqui o comando é a **mensagem**.

> **Cuidado.** Com nova tentativa, um comando pode rodar duas vezes: o worker cai depois de enviar o e-mail e antes de confirmar na fila. Cada comando precisa ser idempotente, ou guardar uma marca de "já feito", ou o cliente recebe dois e-mails.

<a id="varios-gatilhos"></a>
## 3. A mesma ação em botão, menu e atalho

**Situação.** Um editor de documentos na web. "Salvar" está no botão da barra, no menu Arquivo e no atalho Ctrl+S. Uma paleta de comandos (Ctrl+K) precisa listar todas as ações pelo nome e mostrar só as que estão habilitadas naquele momento.

**sem o pattern — a ação escrita em cada gatilho**

```typescript
btnSalvar.addEventListener("click", () => salvar(doc));
menuSalvar.addEventListener("click", () => salvar(doc));

document.addEventListener("keydown", (ev) => {
  if (ev.ctrlKey && ev.key === "s") { ev.preventDefault(); salvar(doc); }
  if (ev.ctrlKey && ev.key === "p") { ev.preventDefault(); exportarPdf(doc); }
});

// "só habilita se há alterações" — em cada lugar que mostra a ação
btnSalvar.disabled = !doc.sujo;
menuSalvar.classList.toggle("desabilitado", !doc.sujo);
// e a paleta? ela teria que ter a própria lista de nomes e de regras
```

**O que dói.** Cada ação é repetida em tantos lugares quantos são os gatilhos, e a regra de "quando está habilitada" é copiada em cada um, e esquecida em algum. A paleta não consegue existir sem uma lista paralela de ações, que vai divergir da real.

**com o pattern — a ação é um valor com nome, atalho e regra**

```typescript
interface Comando {
  id: string;
  rotulo: string;
  atalho?: string;                  // "CTRL+S"
  habilitado(): boolean;
  executar(): void;
}

const comandos: Comando[] = [
  { id: "salvar", rotulo: "Salvar", atalho: "CTRL+S",
    habilitado: () => doc.sujo, executar: () => salvar(doc) },
  { id: "exportar-pdf", rotulo: "Exportar como PDF", atalho: "CTRL+P",
    habilitado: () => true, executar: () => exportarPdf(doc) },
];

// cada gatilho conhece só "um comando"
function ligar(el: HTMLElement, cmd: Comando) {
  el.addEventListener("click", () => cmd.habilitado() && cmd.executar());
}

document.addEventListener("keydown", (ev) => {
  const chave = (ev.ctrlKey ? "CTRL+" : "") + ev.key.toUpperCase();
  const cmd = comandos.find((c) => c.atalho === chave);
  if (cmd?.habilitado()) { ev.preventDefault(); cmd.executar(); }
});

// a paleta é só um filtro sobre a mesma lista
const naPaleta = comandos.filter((c) => c.habilitado()).map((c) => c.rotulo);
```

**O que o comando carrega.** A ação, mais o que a interface precisa saber sobre ela: o nome, o atalho e a condição de estar habilitada. A origem do clique deixa de importar. Uma ação nova é uma entrada na lista, e ela aparece no menu, no atalho e na paleta sem que ninguém ligue nada.

> **Dica.** É o desenho por trás da paleta de comandos de editores como o VS Code: toda ação é registrada com um id, e a interface é gerada a partir desse registro.

<a id="lote-tudo-ou-nada"></a>
## 4. Passos que valem por inteiro ou nada

**Situação.** Transferir estoque entre dois depósitos tem quatro passos: baixar na origem, creditar no destino, registrar a movimentação e recalcular o custo médio. Os depósitos moram em sistemas diferentes, então não há uma transação de banco única que cubra tudo. Se o terceiro passo falha, os dois primeiros já aconteceram.

**sem o pattern — o desfazer escrito à mão, em cada fluxo**

```python
def transferir(origem, destino, sku, qtd):
    origem.baixar(sku, qtd)
    destino.creditar(sku, qtd)
    try:
        auditoria.registrar(origem, destino, sku, qtd)
    except Exception:
        destino.debitar(sku, qtd)       # desfaz na ordem certa... espero
        origem.creditar(sku, qtd)
        raise
    custos.recalcular(sku)              # e se falhar aqui? outro try, com outro desfazer
```

**O que dói.** Cada passo novo muda a estrutura dos `try`: o código de "voltar" fica aninhado e cresce com os passos. Esquecer um passo no `except` deixa o estoque inconsistente, e esse erro só aparece quando a falha acontece de verdade. E o mesmo fluxo, em outra tela, teria a própria cópia.

**com o pattern — a macro é um comando feito de comandos**

```python
class Macro(Comando):
    def __init__(self, *passos: Comando):
        self._passos = passos
        self._feitos: list[Comando] = []

    def executar(self):
        try:
            for passo in self._passos:
                passo.executar()
                self._feitos.append(passo)
        except Exception:
            self.desfazer()               # volta o que já foi, do último para o primeiro
            raise

    def desfazer(self):
        while self._feitos:
            self._feitos.pop().desfazer()

transferencia = Macro(
    BaixarEstoque(origem, sku, qtd),
    CreditarEstoque(destino, sku, qtd),
    RegistrarMovimentacao(origem, destino, sku, qtd),
    RecalcularCusto(sku),
)
historico.executar(transferencia)
```

**O que o comando carrega.** Os próprios passos e a ordem de desfazê-los. Como a `Macro` também é um `Comando`, ela se compõe: o histórico vê a transferência inteira como uma ação, e um Ctrl+Z reverte os quatro passos de uma vez. A regra "do último para o primeiro" vive em um lugar só, e um passo novo é mais uma linha na lista.

> **Cuidado.** A macro só é tão boa quanto o `desfazer` de cada passo. Um passo sem volta, como enviar e-mail, não pode ficar no meio da lista: ponha-o no fim, depois que tudo deu certo, ou fora da macro.

<a id="fora-da-lista"></a>
## O que ficou de fora

Casos comuns que não ganharam seção própria, porque o motivo já está em um dos quatro:

| Caso | Já coberto por |
|---|---|
| Nova tentativa com espera crescente de uma chamada externa | 2 — o pedido guardado como dado é reenviado |
| Log de auditoria que pode ser reaplicado para reconstruir um estado | 2 — a ação serializada, em vez de um texto de log |
| Gravar uma sequência de ações do usuário e reproduzi-la depois | 4 — uma lista de comandos que se executa como um só |
| Esmaecer um botão quando a ação não faz sentido | 3 — a condição de "habilitado" mora no comando |
| Desfazer em um formulário, restaurando os campos | 1 — mas, se o estado é pequeno, o snapshot basta (veja [Quando não usar](explicacao.md#quando-nao-usar)) |

E um caso que parece Command, mas não é: passar uma função de callback para `onClick` ou para `setTimeout`. A ação é um valor, mas ninguém vai desfazê-la, guardá-la ou nomeá-la. Uma função basta, e o objeto só acrescentaria cerimônia. Veja também [Parecidos](explicacao.md#parecidos).
