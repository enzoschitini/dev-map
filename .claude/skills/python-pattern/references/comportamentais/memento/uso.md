<!-- Gerado de pages/clean-code/comportamentais/memento/uso.html por scripts/sync_references.py. Não edite aqui: edite a página e rode o script. -->

# Memento — Uso

*Clean Code / Design Pattern / Memento*

Quatro situações em que o Memento resolve o problema. Cada uma traz o código sem o pattern, o código com ele e o que a foto guarda em cada caso.

<a id="como-escolhi"></a>
## Por que quatro

Cada exemplo entrou com uma regra: precisa trazer um **motivo diferente** para usar o Memento. Quando dois casos se resolvem com o mesmo raciocínio — desfazer em um editor de texto e desfazer em um editor de planilha, por exemplo — só um fica. Seguindo essa regra, sobraram quatro motivos. Os que ficaram de fora estão no [fim da página](#fora-da-lista).

| # | Situação | O que o Memento congela |
|---|---|---|
| 1 | [Histórico barato em um editor com muito estado](#historico-do-editor) | Referências a peças imutáveis, não cópias delas |
| 2 | [Simular o efeito antes de decidir](#simular-e-decidir) | Um ponto de partida para a simulação voltar a ele |
| 3 | [Rascunho que sobrevive ao fechar a aba](#rascunho-que-sobrevive) | Um estado que sai do processo e volta com versão |
| 4 | [Tentar um caminho e voltar se não der](#tentar-e-voltar) | Poucos números privados, muitas vezes por segundo |

<a id="historico-do-editor"></a>
## 1. Histórico barato em um editor com muito estado

**Situação.** Um editor de imagens tem documentos com até 200 camadas, cada uma com seus pixels. Desfazer é a funcionalidade mais usada: a pessoa aplica um filtro, olha e volta. As janelas de camadas e de propriedades guardam referência para o documento aberto e se atualizam quando ele muda.

**sem o pattern — uma cópia profunda a cada clique**

```python
class Editor:
    def __init__(self, documento):
        self.documento = documento
        self._pilha = []

    def aplicar(self, operacao):
        self._pilha.append(copy.deepcopy(self.documento))  # 200 camadas, a cada clique
        operacao(self.documento)

    def desfazer(self):
        if self._pilha:
            self.documento = self._pilha.pop()  # e os painéis, que seguravam o objeto antigo?
```

**O que dói.** Copiar todos os pixels para mudar a opacidade de uma camada é lento e consome memória; com cinquenta passos, o histórico pesa gigabytes. Além disso, `self.documento = …` troca o objeto: os painéis continuam olhando para o documento antigo e mostram o estado de antes do desfazer.

**com o pattern — a foto guarda referências, o documento continua o mesmo**

```python
@dataclass(frozen=True)
class Camada:                # imutável: uma alteração cria outra camada
    nome: str
    pixels: bytes
    opacidade: float = 1.0

@dataclass(frozen=True)
class _Foto:
    camadas: tuple[Camada, ...]   # só referências: nenhum pixel é copiado
    ativa: int

class Documento:
    def __init__(self):
        self._camadas: list[Camada] = []
        self._ativa = 0
        self._miniaturas: dict = {}      # derivado: nunca vai para a foto

    def salvar(self) -> _Foto:
        return _Foto(tuple(self._camadas), self._ativa)

    def restaurar(self, foto: _Foto) -> None:
        self._camadas = list(foto.camadas)
        self._ativa = foto.ativa
        self._miniaturas.clear()         # recalculado quando alguém pedir

class Editor:
    def __init__(self, documento: Documento, limite: int = 50):
        self.documento = documento             # o mesmo objeto, sempre
        self._passado = deque(maxlen=limite)

    def aplicar(self, operacao):
        self._passado.append(self.documento.salvar())
        operacao(self.documento)

    def desfazer(self):
        if self._passado:
            self.documento.restaurar(self._passado.pop())
```

**O que a foto guarda.** Uma tupla de referências. Como a `Camada` é imutável, 49 das 50 fotos apontam para as mesmas 199 camadas que não mudaram, e o custo de um passo é o da tupla, não o dos pixels. O documento nunca é trocado: `restaurar` muda o que há dentro dele, e os painéis, que continuam olhando para o mesmo objeto, só precisam ser avisados.

Para um editor em que cada ação tem uma volta simples, o [Command](../command/uso.md#desfazer-refazer) resolve com menos memória ainda. O Memento vale quando o "inverso" de uma operação é difícil de escrever (um filtro de desfoque não tem inverso) e a foto, graças à imutabilidade, é barata.

> **Cuidado.** O que é *derivado* fica fora da foto, e o `restaurar` o invalida. Só o originador sabe que `_miniaturas` é cache; por isso a regra mora nele e não no editor.

<a id="simular-e-decidir"></a>
## 2. Simular o efeito antes de decidir

**Situação.** O financeiro de uma escola quer saber quanto a receita mensal muda se a mensalidade subir 8%, respeitando o teto por contrato, o arredondamento para o real mais próximo e a carência de contratos novos. A decisão só vem depois de olhar o número. A regra de reajuste é complicada, e já existe e funciona: `Carteira.reajustar`.

**sem o pattern — a simulação é uma segunda cópia da regra**

```python
class Carteira:
    def reajustar(self, pct):
        for c in self._contratos:
            if c.em_carencia():
                continue
            novo = round(c.valor * (1 + pct))
            c.valor = min(novo, c.teto)

    def simular_reajuste(self, pct):
        total = 0
        for c in self._contratos:
            novo = c.valor * (1 + pct)
            total += min(novo, c.teto)   # sem arredondar, sem carência
        return total
```

**O que dói.** A simulação já nasceu diferente da regra: esqueceu o arredondamento e a carência, então o número que a diretoria vê não é o que sai quando o reajuste é aplicado. Cada ajuste na regra real exige lembrar de mexer na cópia, e ninguém tem um teste que compare as duas.

**com o pattern — a regra real roda, e depois tudo volta**

```python
class Carteira:
    def salvar(self) -> tuple[Contrato, ...]:
        return tuple(self._contratos)         # Contrato é frozen

    def restaurar(self, foto) -> None:
        self._contratos = list(foto)

    def reajustar(self, pct):              # a única cópia da regra
        self._contratos = [
            c if c.em_carencia() else replace(c, valor=min(round(c.valor * (1 + pct)), c.teto))
            for c in self._contratos
        ]

@contextmanager
def simulacao(carteira: Carteira):
    foto = carteira.salvar()
    try:
        yield carteira
    finally:
        carteira.restaurar(foto)

with simulacao(carteira):
    carteira.reajustar(0.08)
    projecao = carteira.receita_mensal()
# fora do with, a carteira é a de antes. Para aplicar de verdade: carteira.reajustar(0.08)
```

**O que a foto guarda.** Só o ponto de partida. O trabalho de verdade é feito pelo código real, então a projeção e o resultado aplicado não têm como divergir. O `finally` devolve a carteira até quando `reajustar` lança uma exceção no meio, e é isso que torna seguro experimentar em cima do objeto verdadeiro.

> **Cuidado.** A foto cobre a *carteira*, e nada além dela. Se `reajustar` enviasse e-mail ou gravasse no banco, a simulação já teria feito os dois. A regra para entrar em um `with simulacao` é: tudo o que acontece lá dentro só mexe na memória do objeto.

<a id="rascunho-que-sobrevive"></a>
## 3. Rascunho que sobrevive ao fechar a aba

**Situação.** O cadastro de um imóvel tem quatro etapas, com fotos, endereço, preço e descrição. Quem anuncia leva meia hora, fecha a aba por engano, ou volta no dia seguinte. O produto prometeu "continuar de onde parou". Daqui a três meses o formulário vai ganhar uma quinta etapa.

**sem o pattern — um setItem por campo, em cada etapa**

```typescript
// etapa-1.tsx
localStorage.setItem("cadastro.titulo", titulo);
localStorage.setItem("cadastro.preco", String(preco));

// etapa-3.tsx — esqueceu de salvar as fotos
localStorage.setItem("cadastro.cep", cep);

// ao voltar
const preco = Number(localStorage.getItem("cadastro.preco"));  // null vira 0, em silêncio
const etapa = Number(localStorage.getItem("cadastro.etapa")) || 1;
```

**O que dói.** Cada etapa conhece o formato do armazenamento e a chave que as outras usam. Não existe uma noção de "o rascunho", então não há como apagá-lo inteiro, nem saber se está completo. E, quando a quinta etapa chegar, quem voltar com o rascunho de ontem vai receber um formulário com dados de antes e de depois misturados.

**com o pattern — o estado vira um valor serializável e com versão**

```typescript
// o memento aqui é dado puro: precisa sobreviver ao processo
export interface Rascunho {
  versao: 2;
  etapa: number;
  dados: DadosDoImovel;
}
interface RascunhoV1 { versao: 1; etapa: number; dados: DadosDoImovelV1 }

export class CadastroDeImovel {
  private etapa = 1;
  private dados: DadosDoImovel = vazio();

  salvar(): Rascunho {
    return { versao: 2, etapa: this.etapa, dados: structuredClone(this.dados) };
  }

  restaurar(r: Rascunho | RascunhoV1): void {
    const atual = r.versao === 1 ? migrarV1(r) : r;
    this.etapa = atual.etapa;
    this.dados = structuredClone(atual.dados);
  }
}

// o zelador: grava e lê; não sabe o que tem dentro
const CHAVE = "rascunho.cadastro-imovel";

export const rascunhos = {
  gravar(r: Rascunho) { localStorage.setItem(CHAVE, JSON.stringify(r)); },
  ler(): Rascunho | RascunhoV1 | null {
    const bruto = localStorage.getItem(CHAVE);
    return bruto ? JSON.parse(bruto) : null;
  },
  descartar() { localStorage.removeItem(CHAVE); },
};
```

**O que a foto guarda.** Aqui a foto sai do processo, e isso muda o desenho: ela precisa ser dado puro, sem referência a objetos vivos, e ganha um número de `versao`. O `restaurar` é o único lugar que sabe ler o formato antigo. Quando a quinta etapa chegar, é ali que o rascunho de ontem é migrado, e nenhuma tela é tocada.

> **Cuidado.** O `localStorage` grava texto, no disco da pessoa, sem criptografia. O que entra na foto é uma decisão: CPF, telefone e documentos anexados provavelmente não devem ficar lá.

<a id="tentar-e-voltar"></a>
## 4. Tentar um caminho e voltar se não der

**Situação.** Um parser de filtros — `preco > 10 e total(itens) < 50` — lê uma lista de tokens. Em alguns pontos, a gramática é ambígua: um nome pode ser uma chamada (`total(itens)`) ou um caminho (`cliente.endereco`), e só dá para saber olhando o que vem depois. A saída é tentar uma e, se falhar, voltar e tentar a outra.

**sem o pattern — o parser guarda e devolve cada campo da leitura**

```python
class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0
        self.nivel = 0          # profundidade de parênteses
        self.avisos = []

    def valor(self):
        pos, nivel, n_avisos = self.pos, self.nivel, len(self.avisos)
        try:
            return self.chamada()
        except ErroDeSintaxe:
            self.pos, self.nivel = pos, nivel
            del self.avisos[n_avisos:]
            return self.caminho()

    # e o mesmo bloco de salvar e devolver reaparece em comparacao(),
    # em lista(), em grupo()... cada um com os campos que lembrou
```

**O que dói.** Todo ponto com alternativa repete o "salvar e devolver" com os campos que o autor lembrou na hora. Quando a leitura ganha um novo estado (a linha atual, para mensagens de erro), é preciso achar cada `try` e acrescentar mais uma atribuição. Os que forem esquecidos viram bugs que só aparecem com uma entrada específica.

**com o pattern — a leitura sabe marcar e voltar; o parser só tenta**

```python
@dataclass(frozen=True)
class _Marca:                       # poderia ser uma tupla; o nome só deixa claro
    pos: int
    nivel: int
    avisos: int

class Fita:
    def __init__(self, tokens):
        self._tokens = tokens
        self._pos = 0
        self._nivel = 0
        self._avisos: list[str] = []

    def marcar(self) -> _Marca:
        return _Marca(self._pos, self._nivel, len(self._avisos))

    def voltar(self, marca: _Marca) -> None:
        self._pos, self._nivel = marca.pos, marca.nivel
        del self._avisos[marca.avisos:]

class Parser:
    def __init__(self, fita: Fita):
        self._fita = fita

    def tentar(self, *alternativas):
        for alternativa in alternativas:
            marca = self._fita.marcar()
            try:
                return alternativa()
            except ErroDeSintaxe:
                self._fita.voltar(marca)
        raise ErroDeSintaxe("nenhuma alternativa serve")

    def valor(self):
        return self.tentar(self.chamada, self.caminho)
```

**O que a foto guarda.** Três inteiros privados da leitura, tirados e devolvidos a cada tentativa, muitas vezes por segundo. O custo é desprezível, e por isso aqui o histórico não precisa de limite. O ganho é o mesmo dos outros casos em outra escala: quando a `Fita` ganhar a linha atual, muda `marcar` e `voltar`, e as quatorze alternativas do parser seguem iguais.

> **Dica.** Os motores de expressão regular e os parsers com *backtracking* fazem exatamente isso por dentro: marcam a posição, tentam, voltam. É o Memento em sua forma mais enxuta.

<a id="fora-da-lista"></a>
## O que ficou de fora

Casos comuns que não ganharam seção própria, porque o motivo já está em um dos quatro:

| Caso | Já coberto por |
|---|---|
| Desfazer e refazer em um editor de texto ou de planilha | 1 — o mesmo raciocínio, com outro objeto. Se o documento é grande, guarde só a diferença (Command) |
| "Restaurar padrões de fábrica" em uma tela de configurações | 1 — é voltar a uma foto tirada na abertura |
| Rollback em memória em um teste, para cada caso começar do mesmo ponto | 2 — foto, mexe, restaura |
| Salvar o jogo, ou o ponto de retomada de um processamento longo | 3 — o estado sai do processo e volta com versão |
| Voltar a posição da rolagem e a ordenação da lista ao retornar a uma tela | Nenhum: são dois valores simples. Guarde-os em variáveis; um Memento aqui só acrescenta classes |

E dois casos que parecem Memento, mas não são: copiar um objeto para criar *outro* igual a ele (Prototype), e registrar cada mudança, com autor e data, para auditar o que aconteceu (um log de eventos). Nos dois, a foto não serve para voltar a algum lugar — veja a seção [Parecidos](explicacao.md#parecidos) da explicação.
