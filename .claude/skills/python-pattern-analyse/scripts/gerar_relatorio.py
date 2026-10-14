"""Valida o relatorio.json da skill python-pattern-analyse e gera o relatorio.html.

O HTML sai num arquivo só (CSS e JS embutidos), no visual do DevMap, com tema
claro e escuro. Os trechos de evidência são lidos dos arquivos reais do projeto,
com numeração de linha, para o relatório nunca mostrar código que não existe.

Uso, a partir da raiz do projeto analisado:

    py <skill>/scripts/gerar_relatorio.py docs/refatoracao/<slug>/relatorio.json
    py <skill>/scripts/gerar_relatorio.py <json> --raiz <pasta do projeto> --saida <html>

Sai com código 1 e não escreve o HTML se o JSON tiver erros. Avisos não bloqueiam.
"""

from __future__ import annotations

import argparse
import html
import json
import keyword
import re
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
REFERENCIAS = SKILL_DIR.parent / "python-pattern" / "references"
SITE = "https://enzoschitini.github.io/dev-map/pages/clean-code/"

PRINCIPIOS = [
    ("single-responsibility", "S", "Single Responsibility"),
    ("open-closed", "O", "Open/Closed"),
    ("liskov-substitution", "L", "Liskov Substitution"),
    ("interface-segregation", "I", "Interface Segregation"),
    ("dependency-inversion", "D", "Dependency Inversion"),
]
APELIDOS = {
    "srp": "single-responsibility", "ocp": "open-closed", "lsp": "liskov-substitution",
    "isp": "interface-segregation", "dip": "dependency-inversion",
}
GRUPOS = {"criacionais": "Criacional", "estruturais": "Estrutural", "comportamentais": "Comportamental"}
SEVERIDADES = {"alta": "Alta", "media": "Média", "baixa": "Baixa"}
NIVEIS = {"alto": "Alto", "medio": "Médio", "baixo": "Baixo"}
ESFORCOS = {"P": "Pequeno", "M": "Médio", "G": "Grande"}
EFEITOS = {
    "banco": "banco", "rede": "rede", "email": "e-mail", "disco": "disco", "relogio": "relógio",
    "aleatorio": "aleatório", "env": "ambiente", "stdout": "stdout", "fila": "fila", "cache": "cache",
}


def sem_acento(texto: str) -> str:
    return texto.lower().translate(str.maketrans("áâãàéêíóôõúç", "aaaaeeiooouc")).strip()


# ── catálogo (vem das referências da skill python-pattern) ────────────────────

def carregar_catalogo() -> dict[str, dict]:
    catalogo: dict[str, dict] = {}

    def lead(arquivo: Path) -> str:
        if not arquivo.exists():
            return ""
        blocos = [b.strip() for b in arquivo.read_text(encoding="utf-8").split("\n\n")]
        # comentário, # título, *eyebrow*, lead
        for i, bloco in enumerate(blocos):
            if bloco.startswith("*") and bloco.endswith("*") and i + 1 < len(blocos):
                return blocos[i + 1]
        return ""

    for slug, letra, nome in PRINCIPIOS:
        catalogo[slug] = {
            "slug": slug, "nome": nome, "tipo": "Princípio SOLID", "letra": letra,
            "lead": lead(REFERENCIAS / f"{slug}.md"),
            "links": [("Explicação", f"{SITE}{slug}.html")],
        }
    for grupo, rotulo in GRUPOS.items():
        pasta = REFERENCIAS / grupo
        if not pasta.is_dir():
            continue
        for sub in sorted(pasta.iterdir()):
            explicacao = sub / "explicacao.md"
            if not explicacao.exists():
                continue
            titulo = explicacao.read_text(encoding="utf-8").split("\n# ", 1)[-1].split("\n", 1)[0]
            nome = titulo.split(" — ")[0].strip()
            catalogo[sub.name] = {
                "slug": sub.name, "nome": nome, "tipo": f"Pattern {rotulo.lower()}", "grupo": grupo,
                "lead": lead(explicacao),
                "links": [
                    ("Explicação", f"{SITE}{grupo}/{sub.name}/explicacao.html"),
                    ("Exemplos de uso", f"{SITE}{grupo}/{sub.name}/uso.html"),
                ],
            }
    return catalogo


def normalizar_slug(valor: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", sem_acento(valor)).strip("-")
    return APELIDOS.get(slug, slug)


# ── validação ─────────────────────────────────────────────────────────────────

class Validacao:
    def __init__(self) -> None:
        self.erros: list[str] = []
        self.avisos: list[str] = []

    def erro(self, msg: str) -> None:
        self.erros.append(msg)

    def aviso(self, msg: str) -> None:
        self.avisos.append(msg)


def intervalos(valor) -> set[int]:
    linhas: set[int] = set()
    for item in valor or []:
        if isinstance(item, int):
            linhas.add(item)
        elif isinstance(item, (list, tuple)) and len(item) == 2:
            linhas.update(range(int(item[0]), int(item[1]) + 1))
    return linhas


def validar(dados: dict, raiz: Path, catalogo: dict, v: Validacao) -> None:
    for campo in ("titulo", "data", "escopo", "resumo", "fluxo", "achados", "recomendacoes", "roteiro"):
        if campo not in dados:
            v.erro(f"campo obrigatório ausente: {campo}")
    if v.erros:
        return

    escopo, resumo = dados["escopo"], dados["resumo"]
    if not escopo.get("arquivos"):
        v.erro("escopo.arquivos: liste pelo menos um arquivo analisado")
    for arq in escopo.get("arquivos", []):
        if not (raiz / arq.get("caminho", "")).is_file():
            v.erro(f"escopo.arquivos: arquivo não encontrado a partir da raiz: {arq.get('caminho')}")
    for campo in ("veredito", "texto"):
        if not resumo.get(campo):
            v.erro(f"resumo.{campo} é obrigatório")
    if resumo.get("prioridade") and sem_acento(resumo["prioridade"]) not in SEVERIDADES:
        v.erro(f"resumo.prioridade deve ser alta, media ou baixa (veio {resumo['prioridade']!r})")

    achados = {a.get("id"): a for a in dados["achados"]}
    recs = {r.get("id"): r for r in dados["recomendacoes"]}
    for nome, itens in (("achados", dados["achados"]), ("recomendacoes", dados["recomendacoes"])):
        ids = [i.get("id") for i in itens]
        for repetido in {i for i in ids if ids.count(i) > 1}:
            v.erro(f"{nome}: id repetido {repetido}")
        if None in ids:
            v.erro(f"{nome}: todo item precisa de id")

    descartados_achados = {a for d in dados.get("descartados", []) for a in d.get("achados", [])}

    for etapa in dados["fluxo"].get("etapas", []):
        for a in etapa.get("achados", []):
            if a not in achados:
                v.erro(f"fluxo.etapas[{etapa.get('id')}]: achado inexistente {a}")
        for e in etapa.get("efeitos", []):
            if sem_acento(e) not in EFEITOS:
                v.aviso(f"fluxo.etapas[{etapa.get('id')}]: efeito desconhecido {e!r} (use {', '.join(EFEITOS)})")
    if not dados["fluxo"].get("etapas"):
        v.erro("fluxo.etapas: descreva pelo menos uma etapa")

    for aid, a in achados.items():
        onde = f"achados[{aid}]"
        for campo in ("titulo", "severidade", "sinal", "impacto", "evidencias"):
            if not a.get(campo):
                v.erro(f"{onde}.{campo} é obrigatório")
        if a.get("severidade") and sem_acento(a["severidade"]) not in SEVERIDADES:
            v.erro(f"{onde}.severidade deve ser alta, media ou baixa")
        for p in a.get("principios", []):
            if normalizar_slug(p) not in {s for s, _, _ in PRINCIPIOS}:
                v.erro(f"{onde}.principios: {p!r} não é um princípio SOLID")
        for r in a.get("recomendacoes", []):
            if r not in recs:
                v.erro(f"{onde}.recomendacoes: recomendação inexistente {r}")
        tratado = any(aid in r.get("achados", []) for r in recs.values()) or aid in descartados_achados
        if not tratado:
            v.erro(f"{onde}: nenhum item de recomendacoes ou descartados cita este achado")
        for i, ev in enumerate(a.get("evidencias", [])):
            validar_evidencia(ev, raiz, f"{onde}.evidencias[{i}]", v)

    no_roteiro = {r for passo in dados["roteiro"] for r in passo.get("recomendacoes", [])}
    for rid, r in recs.items():
        onde = f"recomendacoes[{rid}]"
        for campo in ("titulo", "pattern", "achados", "porque", "teste_rapido", "quando_nao_usar", "onde"):
            if not r.get(campo):
                v.erro(f"{onde}.{campo} é obrigatório")
        for a in r.get("achados", []):
            if a not in achados:
                v.erro(f"{onde}.achados: achado inexistente {a}")
        slug = normalizar_slug(r.get("pattern", ""))
        if slug and slug not in catalogo:
            v.aviso(f"{onde}.pattern: {r['pattern']!r} não está na documentação do DevMap; o relatório vai marcá-lo como fora do catálogo")
        if sem_acento(r.get("impacto", "medio")) not in NIVEIS:
            v.erro(f"{onde}.impacto deve ser alto, medio ou baixo")
        if str(r.get("esforco", "M")).upper() not in ESFORCOS:
            v.erro(f"{onde}.esforco deve ser P, M ou G")
        for i, t in enumerate(r.get("teste_rapido", [])):
            if not t.get("pergunta") or not t.get("resposta"):
                v.erro(f"{onde}.teste_rapido[{i}]: pergunta e resposta são obrigatórias")
        if rid not in no_roteiro:
            v.erro(f"{onde}: a recomendação não aparece em nenhum passo do roteiro")
        codigo = r.get("codigo_proposto")
        if codigo and codigo.get("arquivo") and not codigo.get("codigo"):
            v.aviso(f"{onde}.codigo_proposto.arquivo é resolvido a partir da pasta do JSON")

    bugs = dados.get("bugs", [])
    ids_bugs = [b.get("id") for b in bugs]
    for i, b in enumerate(bugs):
        if not b.get("id"):
            v.erro(f"bugs[{i}]: todo bug precisa de id (B1, B2…)")
        elif ids_bugs.count(b["id"]) > 1:
            v.erro(f"bugs: id repetido {b['id']}")
        if b.get("severidade") and sem_acento(b["severidade"]) not in SEVERIDADES:
            v.erro(f"bugs[{b.get('id', i)}].severidade deve ser alta, media ou baixa")
        if not b.get("descricao"):
            v.erro(f"bugs[{b.get('id', i)}].descricao é obrigatória")

    for i, passo in enumerate(dados["roteiro"]):
        for r in passo.get("recomendacoes", []):
            if r not in recs:
                v.erro(f"roteiro[{i}]: recomendação inexistente {r}")
        for b in passo.get("bugs", []):
            if b not in ids_bugs:
                v.erro(f"roteiro[{i}]: bug inexistente {b}")
        if not passo.get("titulo"):
            v.erro(f"roteiro[{i}].titulo é obrigatório")

    # [[A1]], [[R1]], [[B1]] escritos nos textos precisam existir
    existentes = set(achados) | set(recs) | set(ids_bugs)
    for caminho, texto in textos(dados):
        for ref in re.findall(r"\[\[([ARB]\d+)\]\]", texto):
            if ref not in existentes:
                v.erro(f"{caminho}: referência [[{ref}]] não aponta para nenhum achado, recomendação ou bug")

    # o "onde" de etapas, elementos e bugs começa com um caminho de arquivo
    lugares = [(f"fluxo.etapas[{e.get('id')}]", e.get("onde")) for e in dados["fluxo"].get("etapas", [])]
    lugares += [(f"elementos[{e.get('nome')}]", e.get("onde")) for e in dados.get("elementos", [])]
    lugares += [(f"bugs[{b.get('id')}]", b.get("onde")) for b in bugs]
    for onde, valor in lugares:
        if valor:
            caminho = re.split(r"[:\s]", str(valor), maxsplit=1)[0]
            if caminho.endswith(".py") and not (raiz / caminho).is_file():
                v.aviso(f"{onde}.onde: arquivo não encontrado a partir da raiz: {caminho}")

    for i, d in enumerate(dados.get("descartados", [])):
        for campo in ("pattern", "motivo"):
            if not d.get(campo):
                v.erro(f"descartados[{i}].{campo} é obrigatório")
        for a in d.get("achados", []):
            if a not in achados:
                v.erro(f"descartados[{i}].achados: achado inexistente {a}")

    for secao in ("descartados", "contrato", "riscos", "fica_como_esta"):
        if not dados.get(secao) and not (secao == "contrato" and escopo.get("contrato")):
            v.aviso(f"seção {secao} está vazia; um relatório sênior quase sempre tem algo a dizer aqui")


def textos(valor, caminho: str = "") -> list[tuple[str, str]]:
    """Todas as strings do JSON, com o caminho de cada uma (para mensagens de erro)."""
    if isinstance(valor, str):
        return [(caminho or "raiz", valor)]
    if isinstance(valor, dict):
        return [t for k, v in valor.items() for t in textos(v, f"{caminho}.{k}" if caminho else k)]
    if isinstance(valor, list):
        return [t for i, v in enumerate(valor) for t in textos(v, f"{caminho}[{i}]")]
    return []


def entradas(escopo: dict) -> list[str]:
    valor = escopo.get("ponto_de_entrada") or []
    return [valor] if isinstance(valor, str) else list(valor)


def validar_evidencia(ev: dict, raiz: Path, onde: str, v: Validacao) -> None:
    if ev.get("codigo"):
        return
    arquivo = raiz / ev.get("arquivo", "")
    if not ev.get("arquivo") or not arquivo.is_file():
        v.erro(f"{onde}: arquivo não encontrado a partir da raiz: {ev.get('arquivo')}")
        return
    linhas = ev.get("linhas")
    if not (isinstance(linhas, list) and len(linhas) == 2 and all(isinstance(n, int) for n in linhas)):
        v.erro(f"{onde}.linhas deve ser [inicio, fim]")
        return
    total = len(arquivo.read_text(encoding="utf-8", errors="replace").splitlines())
    inicio, fim = linhas
    if not (1 <= inicio <= fim <= total):
        v.erro(f"{onde}.linhas {linhas} fora do arquivo ({total} linhas)")
    fora = [n for n in intervalos(ev.get("destaque")) if not inicio <= n <= fim]
    if fora:
        v.erro(f"{onde}.destaque tem linhas fora do trecho: {sorted(fora)}")


# ── texto e código ────────────────────────────────────────────────────────────

def esc(texto) -> str:
    return html.escape(str(texto), quote=True)


def inline(texto: str, sev: dict[str, str] | None = None) -> str:
    """Markdown mínimo: `código`, **negrito**, *itálico*, [texto](url) e [[A1]] / [[R2]] / [[B3]]."""
    sev = sev or {}
    partes = re.split(r"(`[^`]+`)", str(texto))
    saida = []
    for parte in partes:
        if parte.startswith("`") and parte.endswith("`") and len(parte) > 1:
            saida.append(f"<code>{esc(parte[1:-1])}</code>")
            continue
        t = esc(parte)
        t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)
        t = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"<em>\1</em>", t)
        t = re.sub(r"\[([^\]]+)\]\((https?://[^)\s]+|#[\w-]+)\)", r'<a href="\2">\1</a>', t)
        t = re.sub(
            r"\[\[([ARB]\d+)\]\]",
            lambda m: f'<a class="ref {sev.get(m.group(1), "")}" href="#{m.group(1)}">{m.group(1)}</a>',
            t,
        )
        saida.append(t)
    return "".join(saida)


def bloco(texto: str, sev: dict[str, str] | None = None) -> str:
    """Parágrafos separados por linha em branco; linhas começando com "- " viram lista."""
    if not texto:
        return ""
    if isinstance(texto, list):
        return "<ul>" + "".join(f"<li>{inline(i, sev)}</li>" for i in texto) + "</ul>"
    html_partes = []
    for paragrafo in re.split(r"\n\s*\n", str(texto).strip()):
        linhas = paragrafo.split("\n")
        if all(l.lstrip().startswith("- ") for l in linhas if l.strip()):
            itens = "".join(f"<li>{inline(l.lstrip()[2:], sev)}</li>" for l in linhas if l.strip())
            html_partes.append(f"<ul>{itens}</ul>")
        else:
            html_partes.append(f"<p>{inline(' '.join(l.strip() for l in linhas), sev)}</p>")
    return "".join(html_partes)


TOKEN = re.compile(
    r"""
    (?P<com>\#[^\n]*)
   |(?P<str>(?:[rRbBuUfF]{1,2})?(?:\"\"\"[\s\S]*?\"\"\"|'''[\s\S]*?'''|"(?:\\.|[^"\\\n])*"|'(?:\\.|[^'\\\n])*'))
   |(?P<dec>@[A-Za-z_][\w.]*)
   |(?P<num>\b(?:0[xXoObB][\da-fA-F_]+|\d[\d_]*(?:\.\d*)?(?:[eE][+-]?\d+)?)\b)
   |(?P<word>[A-Za-z_]\w*)
    """,
    re.X,
)
TIPOS_EMBUTIDOS = {"str", "int", "float", "bool", "dict", "list", "tuple", "set", "bytes", "object", "type"}


def realcar(codigo: str) -> list[str]:
    """Realce de Python por regex (funciona em trechos soltos), devolvido linha a linha."""
    segmentos: list[tuple[str, str]] = []
    pos = 0
    anterior = ""
    for m in TOKEN.finditer(codigo):
        if m.start() > pos:
            segmentos.append(("", codigo[pos : m.start()]))
        tipo, valor = m.lastgroup, m.group()
        classe = ""
        if tipo == "com":
            classe = "t-c"
        elif tipo == "str":
            classe = "t-s"
        elif tipo == "num":
            classe = "t-n"
        elif tipo == "dec":
            classe = "t-f"
        elif tipo == "word":
            seguinte = codigo[m.end() :].lstrip(" ")[:1]
            if keyword.iskeyword(valor) or valor in ("match", "case") and seguinte not in "(=.":
                classe = "t-k"
            elif anterior in ("def", "class") or seguinte == "(" or valor[:1].isupper() or valor in TIPOS_EMBUTIDOS:
                classe = "t-f"
            anterior = valor
        segmentos.append((classe, valor))
        pos = m.end()
    segmentos.append(("", codigo[pos:]))

    linhas = [""]
    for classe, valor in segmentos:
        pedacos = valor.split("\n")
        for i, pedaco in enumerate(pedacos):
            if i:
                linhas.append("")
            if pedaco:
                linhas[-1] += f'<span class="{classe}">{esc(pedaco)}</span>' if classe else esc(pedaco)
    return linhas


def desindentar(linhas: list[str]) -> list[str]:
    recuos = [len(l) - len(l.lstrip()) for l in linhas if l.strip()]
    corte = min(recuos) if recuos else 0
    return [l[corte:] for l in linhas]


def bloco_codigo(titulo: str, codigo: str, inicio: int | None = None, destaque: set[int] | None = None,
                 nota: str = "", realce: bool = True) -> str:
    destaque = destaque or set()
    linhas_fonte = codigo.split("\n")
    linhas = realcar("\n".join(linhas_fonte)) if realce else [esc(l) for l in linhas_fonte]
    corpo = []
    for i, conteudo in enumerate(linhas):
        numero = inicio + i if inicio else None
        classes = "ln hl" if numero in destaque else "ln"
        num = f'<span class="n">{numero}</span>' if numero else ""
        corpo.append(f'<span class="{classes}">{num}<span class="lc">{conteudo or " "}</span></span>')
    com_numero = " numbered" if inicio else ""
    cabeca = f'<div class="code-head"><span class="code-title">{titulo}</span><button class="copy" type="button" aria-label="Copiar código">Copiar</button></div>'
    rodape = f'<div class="code-note">{inline(nota)}</div>' if nota else ""
    texto_puro = esc("\n".join(linhas_fonte))
    return (
        f'<figure class="code{com_numero}">{cabeca}<div class="code-body"><pre><code>{"".join(corpo)}</code></pre>'
        f'<textarea class="raw" hidden>{texto_puro}</textarea></div>{rodape}</figure>'
    )


def evidencia(ev: dict, raiz: Path) -> str:
    if ev.get("codigo"):
        titulo = esc(ev.get("titulo") or ev.get("arquivo") or "trecho")
        return bloco_codigo(titulo, ev["codigo"].rstrip("\n"), nota=ev.get("nota", ""))
    arquivo = raiz / ev["arquivo"]
    inicio, fim = ev["linhas"]
    todas = arquivo.read_text(encoding="utf-8", errors="replace").splitlines()
    trecho = desindentar(todas[inicio - 1 : fim])
    titulo = f'<code>{esc(ev["arquivo"])}</code> · linhas {inicio}–{fim}' if fim != inicio else f'<code>{esc(ev["arquivo"])}</code> · linha {inicio}'
    return bloco_codigo(titulo, "\n".join(trecho), inicio, intervalos(ev.get("destaque")), ev.get("nota", ""))


# ── seções ────────────────────────────────────────────────────────────────────

def pill(texto: str, classe: str) -> str:
    return f'<span class="pill {classe}">{esc(texto)}</span>'


def sev_de(valor: str) -> str:
    return sem_acento(valor or "media")


def nome_pattern(valor: str, catalogo: dict) -> tuple[str, dict | None]:
    slug = normalizar_slug(valor)
    item = catalogo.get(slug)
    return (item["nome"] if item else valor), item


def secao(id_: str, numero: int, titulo: str, conteudo: str, intro: str = "") -> str:
    intro_html = f'<p class="section-lead">{intro}</p>' if intro else ""
    return f'<section id="{id_}" class="section"><h2><span class="num">{numero:02d}</span>{esc(titulo)}</h2>{intro_html}{conteudo}</section>'


def contar_linhas(raiz: Path, caminho: str) -> int:
    try:
        return len((raiz / caminho).read_text(encoding="utf-8", errors="replace").splitlines())
    except OSError:
        return 0


def render(dados: dict, raiz: Path, pasta_json: Path, catalogo: dict) -> str:
    achados = dados["achados"]
    recs = dados["recomendacoes"]
    sev = {a["id"]: f"sev-{sev_de(a.get('severidade'))}" for a in achados}
    sev.update({r["id"]: "rec" for r in recs})
    sev.update({b["id"]: f"sev-{sev_de(b.get('severidade'))}" for b in dados.get("bugs", [])})
    pontos_de_entrada = " ".join(f"<code>{esc(p)}</code>" for p in entradas(dados["escopo"])) or "—"
    escopo, resumo, fluxo = dados["escopo"], dados["resumo"], dados["fluxo"]
    arquivos = escopo["arquivos"]
    total_linhas = sum(contar_linhas(raiz, a["caminho"]) for a in arquivos)

    secoes: list[tuple[str, str]] = []  # (id, título) para o índice
    corpo: list[str] = []

    def add(id_: str, titulo: str, conteudo: str, intro: str = "") -> None:
        secoes.append((id_, titulo))
        corpo.append(secao(id_, len(secoes), titulo, conteudo, intro))

    # 1. resumo executivo
    prioridade = sev_de(resumo.get("prioridade", "media"))
    contagem = {k: sum(1 for a in achados if sev_de(a.get("severidade")) == k) for k in SEVERIDADES}
    barra = "".join(
        f'<span class="seg sev-{k}" style="flex:{n}" title="{SEVERIDADES[k]}: {n}"></span>' for k, n in contagem.items() if n
    )
    legenda = " · ".join(f'<span class="dot sev-{k}"></span>{n} {SEVERIDADES[k].lower()}' for k, n in contagem.items())
    patterns_usados = []
    for r in recs:
        nome, _ = nome_pattern(r["pattern"], catalogo)
        if nome not in patterns_usados:
            patterns_usados.append(nome)
    kpis = f"""
      <div class="kpis">
        <div class="kpi"><div class="kpi-label">Achados</div><div class="kpi-value">{len(achados)}</div>
          <div class="bar">{barra}</div><div class="kpi-foot">{legenda}</div></div>
        <div class="kpi"><div class="kpi-label">Recomendações</div><div class="kpi-value">{len(recs)}</div>
          <div class="kpi-foot">{esc(", ".join(patterns_usados))}</div></div>
        <div class="kpi"><div class="kpi-label">Esforço estimado</div><div class="kpi-value small">{esc(resumo.get("esforco", "—"))}</div>
          <div class="kpi-foot">{len(dados["roteiro"])} passos no roteiro</div></div>
        <div class="kpi"><div class="kpi-label">Risco da refatoração</div><div class="kpi-text">{inline(resumo.get("risco", "—"))}</div></div>
      </div>"""
    destaques = "".join(f"<li>{inline(d, sev)}</li>" for d in resumo.get("destaques", []))
    solid = []
    for slug, letra, nome in PRINCIPIOS:
        ids = [a["id"] for a in achados if slug in [normalizar_slug(p) for p in a.get("principios", [])]]
        if ids:
            pior = min((sev_de(next(a for a in achados if a["id"] == i).get("severidade")) for i in ids), key=list(SEVERIDADES).index)
            refs = " ".join(f'<a class="ref {sev[i]}" href="#{i}">{i}</a>' for i in ids)
            solid.append(f'<div class="solid sev-{pior}"><div class="solid-letter">{letra}</div><div><div class="solid-name">{nome}</div><div class="solid-refs">{len(ids)} {"achado" if len(ids) == 1 else "achados"} · {refs}</div></div></div>')
        else:
            solid.append(f'<div class="solid ok"><div class="solid-letter">{letra}</div><div><div class="solid-name">{nome}</div><div class="solid-refs">sem violação relevante</div></div></div>')
    add("resumo", "Resumo executivo", f"""
      <div class="verdict sev-{prioridade}">
        <div class="verdict-kicker">Veredito · prioridade {SEVERIDADES[prioridade].lower()}</div>
        <div class="verdict-title">{inline(resumo["veredito"])}</div>
      </div>
      <div class="prose">{bloco(resumo["texto"], sev)}</div>
      {kpis}
      {"<h3>Principais pontos</h3><ul class='highlights'>" + destaques + "</ul>" if destaques else ""}
      <h3>SOLID neste fluxo</h3>
      <div class="solid-grid">{"".join(solid)}</div>""")

    # 2. escopo
    linhas_arquivos = "".join(
        f'<tr><td><code>{esc(a["caminho"])}</code></td><td class="num">{contar_linhas(raiz, a["caminho"])}</td>'
        f'<td>{inline(a.get("papel", ""), sev)}</td></tr>'
        for a in arquivos
    )
    contrato = dados.get("contrato") or escopo.get("contrato") or []
    fora = escopo.get("fora_do_escopo") or []
    add("escopo", "Escopo e contrato", f"""
      <div class="table-wrap"><table>
        <thead><tr><th>Arquivo</th><th class="num">Linhas</th><th>Papel no fluxo</th></tr></thead>
        <tbody>{linhas_arquivos}</tbody></table></div>
      <div class="grid-2">
        <div class="card"><h3>Testes existentes</h3>{bloco(escopo.get("testes", "Não informado."), sev)}</div>
        <div class="card"><h3>Fora do escopo</h3>{bloco(fora, sev) if fora else "<p class='muted'>Nada além dos arquivos acima.</p>"}</div>
      </div>
      <h3>Contrato a preservar</h3>
      <p class="muted">O que a refatoração não pode mudar, porque alguém de fora depende disso.</p>
      {bloco(contrato, sev) if contrato else "<p class='muted'>Não informado.</p>"}""",
        intro=f'{len(arquivos)} {"arquivo" if len(arquivos) == 1 else "arquivos"}, {total_linhas} linhas. Ponto de entrada: {pontos_de_entrada}.')

    # 3. fluxo
    etapas = []
    for i, e in enumerate(fluxo["etapas"], 1):
        efeitos = "".join(pill(EFEITOS.get(sem_acento(x), x), "effect") for x in e.get("efeitos", []))
        refs = " ".join(f'<a class="ref {sev.get(a, "")}" href="#{a}">{a}</a>' for a in e.get("achados", []))
        io = ""
        if e.get("entrada") or e.get("saida"):
            io = f'<div class="step-io">{inline(e.get("entrada", "—"))} <span class="arrow">→</span> {inline(e.get("saida", "—"))}</div>'
        etapas.append(f"""
          <li class="step">
            <div class="step-n">{i}</div>
            <div class="step-body">
              <div class="step-head"><span class="step-title">{inline(e.get("nome", ""))}</span>{f'<code class="where">{esc(e["onde"])}</code>' if e.get("onde") else ""}</div>
              {f'<div class="step-desc">{inline(e["descricao"], sev)}</div>' if e.get("descricao") else ""}
              {io}
              <div class="step-tags">{efeitos}{('<span class="refs">' + refs + '</span>') if refs else ""}</div>
            </div>
          </li>""")
    add("fluxo", "O fluxo hoje", f'<div class="prose">{bloco(fluxo.get("descricao", ""), sev)}</div><ol class="stepper">{"".join(etapas)}</ol>',
        intro="As etapas na ordem em que acontecem, com os efeitos colaterais de cada uma e os achados que as atingem.")

    # 4. elementos
    if dados.get("elementos"):
        linhas = []
        for el in dados["elementos"]:
            resp = el.get("responsabilidades", [])
            atores = {r.get("ator") for r in resp if r.get("ator")}
            itens = "".join(
                f'<li>{inline(r.get("descricao", ""), sev)}{pill(r["ator"], "actor") if r.get("ator") else ""}</li>' for r in resp
            )
            alerta = pill(f"{len(atores)} motivos para mudar", "warn") if len(atores) > 1 else ""
            onde = f'<div class="muted small">{esc(el.get("tipo", ""))} · <code>{esc(el.get("onde", ""))}</code></div>' if el.get("onde") else ""
            linhas.append(f'<tr><td><code class="strong">{esc(el.get("nome", ""))}</code>{onde}{alerta}</td><td><ul class="resp">{itens}</ul></td></tr>')
        add("elementos", "Elementos e responsabilidades", f"""
          <div class="table-wrap"><table class="elements">
            <thead><tr><th>Elemento</th><th>Responsabilidades e quem pede mudança</th></tr></thead>
            <tbody>{"".join(linhas)}</tbody></table></div>""",
            intro="Para cada elemento, a pergunta do Single Responsibility: quem pede mudança aqui, e por quê? Mais de um ator é sinal de responsabilidades misturadas.")

    # 5. diagnóstico
    cartoes = []
    for a in achados:
        s = sev_de(a.get("severidade"))
        principios = "".join(
            pill(catalogo.get(normalizar_slug(p), {"nome": p})["nome"], "principle") for p in a.get("principios", [])
        )
        resolvido_por = [r["id"] for r in recs if a["id"] in r.get("achados", [])]
        descartado = [d for d in dados.get("descartados", []) if a["id"] in d.get("achados", [])]
        destino = " ".join(f'<a class="ref rec" href="#{r}">{r}</a>' for r in resolvido_por)
        if not destino and descartado:
            destino = '<a class="ref" href="#descartados">ver descartados</a>'
        evs = "".join(evidencia(ev, raiz) for ev in a.get("evidencias", []))
        cartoes.append(f"""
          <article class="finding" id="{esc(a["id"])}" data-sev="{s}">
            <header class="finding-head">
              <span class="id sev-{s}">{esc(a["id"])}</span>
              <h3>{inline(a["titulo"])}</h3>
              {pill(SEVERIDADES[s], f"sev sev-{s}")}
            </header>
            <div class="finding-meta">{principios}{pill(a["categoria"], "category") if a.get("categoria") else ""}</div>
            <div class="signal"><span class="label">Sinal</span>{inline(a["sinal"], sev)}</div>
            {evs}
            <div class="impact"><span class="label">O que dói</span>{bloco(a["impacto"], sev)}</div>
            <div class="finding-foot"><span class="label">Tratado em</span>{destino}</div>
          </article>""")
    filtros = "".join(
        f'<button type="button" class="chip" data-filter="{k}">{v} <span>{contagem[k]}</span></button>' for k, v in SEVERIDADES.items()
    )
    add("diagnostico", "Diagnóstico", f"""
      <div class="filters" role="group" aria-label="Filtrar por severidade"><button type="button" class="chip on" data-filter="todos">Todos <span>{len(achados)}</span></button>{filtros}</div>
      <div class="findings">{"".join(cartoes)}</div>""",
        intro="Cada achado parte de um sinal concreto no código, com a evidência lida do arquivo e a consequência prática.")

    # 6. recomendações
    matriz = {(i, e): [] for i in NIVEIS for e in ESFORCOS}
    for r in recs:
        matriz[(sem_acento(r.get("impacto", "medio")), str(r.get("esforco", "M")).upper())].append(r)
    celulas = []
    for i in NIVEIS:
        for e in ESFORCOS:
            chips = "".join(
                f'<a class="mchip" href="#{r["id"]}"><b>{esc(r["id"])}</b> {esc(nome_pattern(r["pattern"], catalogo)[0])}</a>'
                for r in matriz[(i, e)]
            )
            destaque = " quick" if i == "alto" and e in ("P", "M") else ""
            celulas.append(f'<div class="cell{destaque}">{chips}</div>')
    eixo_y = "".join(f"<div>{v}</div>" for v in NIVEIS.values())
    eixo_x = "".join(f"<div>{v}</div>" for v in ESFORCOS.values())
    matriz_html = f"""
      <div class="matrix-wrap">
        <div class="matrix-y"><span class="axis-title">Impacto</span>{eixo_y}</div>
        <div class="matrix">{"".join(celulas)}</div>
        <div class="matrix-x"><div></div>{eixo_x}</div>
        <div class="matrix-caption">Esforço →  · em destaque: alto impacto com esforço pequeno ou médio, que é por onde começar.</div>
      </div>"""
    cartoes = []
    for r in sorted(recs, key=lambda r: r.get("prioridade", 99)):
        nome, item = nome_pattern(r["pattern"], catalogo)
        tipo = item["tipo"] if item else "fora do catálogo do DevMap"
        teste = "".join(
            f'<li class="{"yes" if t.get("ok", True) else "no"}"><span class="mark">{"✓" if t.get("ok", True) else "✗"}</span>'
            f'<div><div class="q">{inline(t["pergunta"])}</div><div class="a">{inline(t["resposta"], sev)}</div></div></li>'
            for t in r.get("teste_rapido", [])
        )
        papeis = ""
        if r.get("papeis"):
            papeis = "<h4>Papéis no código</h4><div class='table-wrap'><table><thead><tr><th>Papel</th><th>No código</th></tr></thead><tbody>" + "".join(
                f'<tr><td>{inline(p.get("papel", ""))}</td><td>{inline(p.get("no_codigo", ""), sev)}</td></tr>' for p in r["papeis"]
            ) + "</tbody></table></div>"
        codigo = ""
        cp = r.get("codigo_proposto")
        if cp:
            texto = cp.get("codigo")
            if not texto and cp.get("arquivo"):
                caminho = pasta_json / cp["arquivo"]
                texto = caminho.read_text(encoding="utf-8") if caminho.is_file() else f"# arquivo não encontrado: {cp['arquivo']}"
            codigo = "<h4>Como fica</h4>" + bloco_codigo(esc(cp.get("titulo", "proposta")), (texto or "").rstrip("\n"), nota=cp.get("nota", ""))
        onde = r.get("onde")
        onde_html = bloco(onde if isinstance(onde, list) else [onde], sev)
        resolve = " ".join(f'<a class="ref {sev.get(a, "")}" href="#{a}">{a}</a>' for a in r.get("achados", []))
        links = " · ".join(f'<a href="{u}" target="_blank" rel="noopener">{t}</a>' for t, u in (item["links"] if item else []))
        impacto = sem_acento(r.get("impacto", "medio"))
        esforco = str(r.get("esforco", "M")).upper()
        cartoes.append(f"""
          <article class="rec-card" id="{esc(r["id"])}">
            <header class="rec-head">
              <span class="id rec">{esc(r["id"])}</span>
              <div class="rec-titles"><h3>{inline(r["titulo"])}</h3>
                <div class="rec-pattern"><span class="pattern-name">{esc(nome)}</span><span class="muted">{esc(tipo)}</span></div></div>
              <div class="rec-badges">{pill("Impacto " + NIVEIS[impacto].lower(), "lvl-" + impacto)}{pill("Esforço " + ESFORCOS[esforco].lower(), "effort")}</div>
            </header>
            <div class="rec-grid">
              <div><h4>Resolve</h4><p>{resolve}</p><h4>Onde</h4>{onde_html}</div>
              <div><h4>Por que este pattern</h4>{bloco(r["porque"], sev)}</div>
            </div>
            <h4>Teste rápido</h4><p class="muted small">As perguntas da página do pattern, em ordem. ✓ a resposta deixa seguir; ✗ a resposta manda parar.</p><ul class="quicktest">{teste}</ul>
            {papeis}
            {codigo}
            <div class="callout warn"><div class="callout-title">Custo e quando não usar</div>{bloco(r["quando_nao_usar"], sev)}{bloco(r.get("custo", ""), sev)}</div>
            {f'<div class="rec-links">Documentação: {links}</div>' if links else ""}
          </article>""")
    add("recomendacoes", "Recomendações", matriz_html + f'<div class="recs">{"".join(cartoes)}</div>',
        intro="Cada recomendação resolve achados do diagnóstico, passou pelo Teste rápido do pattern e diz o custo que traz.")

    # 7. descartados
    if dados.get("descartados"):
        def refs_de(ids: list[str]) -> str:
            return " ".join('<a class="ref {}" href="#{}">{}</a>'.format(sev.get(a, ""), esc(a), esc(a)) for a in ids)

        linhas = "".join(
            f'<tr><td><strong>{esc(nome_pattern(d["pattern"], catalogo)[0])}</strong></td>'
            f'<td>{inline(d.get("sinal", ""), sev)} {refs_de(d.get("achados", []))}</td>'
            f'<td>{inline(d["motivo"], sev)}</td><td>{inline(d.get("gatilho", "—"), sev)}</td></tr>'
            for d in dados["descartados"]
        )
        add("descartados", "Considerados e descartados", f"""
          <div class="table-wrap"><table>
            <thead><tr><th>Pattern</th><th>Sinal visto</th><th>Por que não agora</th><th>Gatilho para rever</th></tr></thead>
            <tbody>{linhas}</tbody></table></div>""",
            intro="Patterns que pareciam caber e não passaram no Teste rápido ou caíram em \"Quando não usar\". Saber o que não fazer faz parte da proposta.")

    # 8. arquitetura
    arq = dados.get("arquitetura")
    if arq:
        lados = ""
        if arq.get("antes") or arq.get("depois"):
            lados = '<div class="grid-2">' + bloco_codigo("Hoje", arq.get("antes", "").rstrip("\n"), realce=False) + bloco_codigo("Proposta", arq.get("depois", "").rstrip("\n"), realce=False) + "</div>"
        montagem = f'<div class="callout tip"><div class="callout-title">Ponto de montagem</div>{bloco(arq["montagem"], sev)}</div>' if arq.get("montagem") else ""
        add("arquitetura", "Arquitetura proposta", f'<div class="prose">{bloco(arq.get("descricao", ""), sev)}</div>{lados}{montagem}')

    # 9. roteiro
    passos = []
    for i, p in enumerate(dados["roteiro"]):
        refs = " ".join(f'<a class="ref rec" href="#{r}">{r}</a>' for r in p.get("recomendacoes", []))
        refs += " ".join(f' <a class="ref {sev.get(b, "")}" href="#{b}">{b}</a>' for b in p.get("bugs", []))
        esforco = str(p.get("esforco", "")).upper()
        passos.append(f"""
          <li class="road-step">
            <div class="road-n">{esc(p.get("passo", i))}</div>
            <div class="road-body">
              <div class="road-head"><strong>{inline(p["titulo"])}</strong>{pill("Esforço " + ESFORCOS[esforco].lower(), "effort") if esforco in ESFORCOS else ""}{refs}</div>
              {bloco(p.get("descricao", ""), sev)}
              {f'<div class="muted small">Verificação: {inline(p["verificacao"], sev)}</div>' if p.get("verificacao") else ""}
            </div>
          </li>""")
    add("roteiro", "Roteiro de implementação", f'<ol class="roadmap">{"".join(passos)}</ol>',
        intro="A ordem segue o retorno: primeiro a rede de segurança, depois separar responsabilidades, inverter dependências e só então os patterns. Cada passo termina com os testes verdes.")

    # 10. riscos, bugs e o que fica
    partes = []
    if dados.get("riscos"):
        partes.append("<h3>Riscos</h3><div class='table-wrap'><table><thead><tr><th>Risco</th><th>Mitigação</th></tr></thead><tbody>" + "".join(
            f'<tr><td>{inline(x.get("risco", ""), sev)}</td><td>{inline(x.get("mitigacao", ""), sev)}</td></tr>' for x in dados["riscos"]
        ) + "</tbody></table></div>")
    if dados.get("bugs"):
        linhas_bugs = []
        for x in dados["bugs"]:
            s = sev_de(x.get("severidade"))
            linhas_bugs.append(
                f'<tr id="{esc(x["id"])}" class="bug-row"><td><span class="id sev-{s}">{esc(x["id"])}</span></td>'
                f'<td><code>{esc(x.get("onde", ""))}</code></td><td>{inline(x.get("descricao", ""), sev)}</td>'
                f'<td>{inline(x.get("impacto", ""), sev)}</td><td>{pill(SEVERIDADES[s], f"sev sev-{s}")}</td></tr>'
            )
        partes.append("<h3>Bugs e comportamentos estranhos</h3><div class='callout danger'><div class='callout-title'>Fora da refatoração</div><p>Achados durante a análise. A refatoração preserva o comportamento atual; cada correção deve ser um passo próprio, decidido à parte.</p></div><div class='table-wrap'><table><thead><tr><th>Id</th><th>Onde</th><th>O que acontece</th><th>Impacto</th><th>Severidade</th></tr></thead><tbody>"
                      + "".join(linhas_bugs) + "</tbody></table></div>")
    if dados.get("fica_como_esta"):
        partes.append("<h3>O que fica como está</h3><div class='table-wrap'><table><thead><tr><th>Elemento</th><th>Por que não mexer</th></tr></thead><tbody>" + "".join(
            f'<tr><td><code>{esc(x.get("elemento", ""))}</code></td><td>{inline(x.get("motivo", ""), sev)}</td></tr>' for x in dados["fica_como_esta"]
        ) + "</tbody></table></div>")
    if partes:
        add("riscos", "Riscos, bugs e o que fica", "".join(partes))

    # apêndice: glossário
    citados = []
    for a in achados:
        citados += [normalizar_slug(p) for p in a.get("principios", [])]
    citados += [normalizar_slug(r["pattern"]) for r in recs]
    citados += [normalizar_slug(d["pattern"]) for d in dados.get("descartados", [])]
    vistos = []
    for slug in citados:
        if slug in catalogo and slug not in vistos:
            vistos.append(slug)
    if vistos:
        itens = "".join(
            f'<div class="gloss"><div class="gloss-type">{esc(catalogo[s]["tipo"])}</div><div class="gloss-name">{esc(catalogo[s]["nome"])}</div>'
            f'<p>{inline(catalogo[s]["lead"])}</p><div class="gloss-links">'
            + " · ".join(f'<a href="{u}" target="_blank" rel="noopener">{t}</a>' for t, u in catalogo[s]["links"])
            + "</div></div>"
            for s in vistos
        )
        add("glossario", "Glossário", f'<div class="gloss-grid">{itens}</div>',
            intro="Os princípios e patterns citados neste relatório, como estão na documentação do DevMap.")

    toc = "".join(f'<li><a href="#{i}"><span>{n:02d}</span>{esc(t)}</a></li>' for n, (i, t) in enumerate(secoes, 1))
    meta = [
        ("Projeto", esc(dados.get("projeto", "—"))),
        ("Ponto de entrada" if len(entradas(escopo)) < 2 else "Pontos de entrada", pontos_de_entrada),
        ("Escopo", f'{len(arquivos)} {"arquivo" if len(arquivos) == 1 else "arquivos"} · {total_linhas} linhas'),
        ("Data", esc(dados["data"])),
    ]
    if dados.get("autor"):
        meta.append(("Análise", esc(dados["autor"])))
    meta_html = "".join(f"<div><dt>{k}</dt><dd>{v}</dd></div>" for k, v in meta)

    return PAGINA.format(
        titulo=esc(dados["titulo"]),
        css=CSS,
        js=JS,
        toc=toc,
        lead=inline(escopo.get("descricao", ""), sev),
        meta=meta_html,
        corpo="".join(corpo),
        data=esc(dados["data"]),
    )


# ── moldura ───────────────────────────────────────────────────────────────────

PAGINA = """<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Análise de refatoração · {titulo}</title>
<script>
  (function () {{
    var t = null;
    try {{ t = localStorage.getItem('devmap-theme'); }} catch (e) {{}}
    if (t) document.documentElement.dataset.theme = t;
  }})();
</script>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Geist:wght@500;600;700&family=IBM+Plex+Mono:wght@400;500&family=Inter:wght@400;500;600&display=swap">
<style>{css}</style>
</head>
<body>
<header class="topbar">
  <div class="brand"><span class="logo">DM</span><span>DevMap <span class="muted">· Relatório de refatoração</span></span></div>
  <div class="top-actions">
    <button type="button" class="ghost" id="print">Imprimir</button>
    <button type="button" class="ghost" id="theme" aria-label="Alternar tema">Tema</button>
  </div>
</header>
<div class="layout">
  <nav class="toc" aria-label="Seções do relatório"><div class="toc-title">Neste relatório</div><ol>{toc}</ol></nav>
  <main>
    <section class="hero">
      <div class="eyebrow">Análise de código Python · SOLID e Design Patterns</div>
      <h1>{titulo}</h1>
      <p class="lead">{lead}</p>
      <dl class="meta">{meta}</dl>
    </section>
    {corpo}
    <footer class="foot">Gerado em {data} pela skill <code>python-pattern-analyse</code>. Nenhum arquivo do projeto foi alterado durante a análise.</footer>
  </main>
</div>
<script>{js}</script>
</body>
</html>
"""

CSS = """
:root {
  --font-head: "Geist", "Inter", system-ui, sans-serif;
  --font-body: "Inter", system-ui, -apple-system, "Segoe UI", sans-serif;
  --font-mono: "IBM Plex Mono", ui-monospace, "Cascadia Code", Consolas, monospace;
  --bg: #ffffff; --bg-2: #f8f8fa; --ink: #030710; --ink-2: #3f3f40; --ink-3: #707071;
  --line: rgba(11,12,14,.1); --line-soft: #eeeeef; --fill: #f3f3f4;
  --primary: #161f34; --accent: #4b61d1; --accent-fill: rgba(75,97,209,.09);
  --code-bg: #ffffff; --code-ink: #4c4f69; --t-c: #72758b; --t-s: #368724; --t-k: #8839ef; --t-n: #ce4c01; --t-f: #1e66f5;
  --hl: rgba(255,196,0,.16); --hl-bd: #e0a400;
  --note-bg: #f4f4f5; --note-bd: #dedee2; --note-ic: #707071;
  --info-bg: #ebf1ff; --info-bd: #b6c8f7; --info-ic: #3552c8;
  --tip-bg: #e8f6ec; --tip-bd: #a5d8b6; --tip-ic: #1d7a48;
  --warn-bg: #fff5dd; --warn-bd: #ecd08a; --warn-ic: #96600b;
  --danger-bg: #ffecec; --danger-bd: #f3b4b1; --danger-ic: #b9362e;
  --r-sm: 10px; --r-md: 12px; --r-lg: 16px;
  color-scheme: light;
}
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    --bg: #030710; --bg-2: #080c18; --ink: #eceef3; --ink-2: #c5c7ce; --ink-3: #9193a0;
    --line: rgba(255,255,255,.1); --line-soft: rgba(255,255,255,.07); --fill: rgba(255,255,255,.05);
    --primary: #eceef3; --accent: #93a4ff; --accent-fill: rgba(147,164,255,.12);
    --code-bg: #0a0e1a; --code-ink: #cdd6f4; --t-c: #8a90ad; --t-s: #a6e3a1; --t-k: #cba6f7; --t-n: #fab387; --t-f: #89b4fa;
    --hl: rgba(250,179,135,.14); --hl-bd: #fab387;
    --note-bg: rgba(255,255,255,.05); --note-bd: rgba(255,255,255,.12); --note-ic: #9193a0;
    --info-bg: rgba(75,97,209,.16); --info-bd: rgba(120,140,240,.4); --info-ic: #9fb0ff;
    --tip-bg: rgba(46,160,98,.15); --tip-bd: rgba(80,190,130,.38); --tip-ic: #7fdcaa;
    --warn-bg: rgba(214,150,30,.14); --warn-bd: rgba(230,175,70,.38); --warn-ic: #f0c577;
    --danger-bg: rgba(220,70,60,.15); --danger-bd: rgba(240,110,100,.4); --danger-ic: #ff9e97;
    color-scheme: dark;
  }
}
:root[data-theme="dark"] {
  --bg: #030710; --bg-2: #080c18; --ink: #eceef3; --ink-2: #c5c7ce; --ink-3: #9193a0;
  --line: rgba(255,255,255,.1); --line-soft: rgba(255,255,255,.07); --fill: rgba(255,255,255,.05);
  --primary: #eceef3; --accent: #93a4ff; --accent-fill: rgba(147,164,255,.12);
  --code-bg: #0a0e1a; --code-ink: #cdd6f4; --t-c: #8a90ad; --t-s: #a6e3a1; --t-k: #cba6f7; --t-n: #fab387; --t-f: #89b4fa;
  --hl: rgba(250,179,135,.14); --hl-bd: #fab387;
  --note-bg: rgba(255,255,255,.05); --note-bd: rgba(255,255,255,.12); --note-ic: #9193a0;
  --info-bg: rgba(75,97,209,.16); --info-bd: rgba(120,140,240,.4); --info-ic: #9fb0ff;
  --tip-bg: rgba(46,160,98,.15); --tip-bd: rgba(80,190,130,.38); --tip-ic: #7fdcaa;
  --warn-bg: rgba(214,150,30,.14); --warn-bd: rgba(230,175,70,.38); --warn-ic: #f0c577;
  --danger-bg: rgba(220,70,60,.15); --danger-bd: rgba(240,110,100,.4); --danger-ic: #ff9e97;
  color-scheme: dark;
}
* { box-sizing: border-box; }
html { scroll-behavior: smooth; scroll-padding-top: 72px; }
body { margin: 0; background: var(--bg); color: var(--ink); font: 400 1rem/1.65 var(--font-body); -webkit-font-smoothing: antialiased; }
a { color: var(--accent); text-underline-offset: 3px; }
code { font-family: var(--font-mono); font-size: .86em; background: var(--fill); border: 1px solid var(--line-soft); padding: .08em .38em; border-radius: 6px; overflow-wrap: anywhere; }
h1, h2, h3, h4 { font-family: var(--font-head); letter-spacing: -.02em; color: var(--ink); }
h3 { font-size: 1.125rem; margin: 28px 0 12px; }
h4 { font-size: .8125rem; text-transform: uppercase; letter-spacing: .06em; color: var(--ink-3); margin: 22px 0 8px; font-family: var(--font-body); }
p { margin: 0 0 12px; }
ul { margin: 0 0 12px; padding-left: 20px; }
.muted { color: var(--ink-3); }
.small { font-size: .8125rem; }

.topbar { position: sticky; top: 0; z-index: 10; display: flex; justify-content: space-between; align-items: center; gap: 12px; padding: 12px 24px; background: color-mix(in srgb, var(--bg) 88%, transparent); backdrop-filter: blur(10px); border-bottom: 1px solid var(--line-soft); }
.brand { display: flex; align-items: center; gap: 10px; font: 600 .9375rem var(--font-head); }
.logo { display: grid; place-items: center; width: 28px; height: 28px; border-radius: 8px; background: var(--primary); color: var(--bg); font-size: .75rem; }
.top-actions { display: flex; gap: 8px; }
.ghost { font: 500 .8125rem var(--font-body); color: var(--ink-2); background: transparent; border: 1px solid var(--line); border-radius: var(--r-sm); padding: 6px 12px; cursor: pointer; }
.ghost:hover { background: var(--fill); }

.layout { display: grid; grid-template-columns: 230px minmax(0, 1fr); gap: 48px; max-width: 1240px; margin: 0 auto; padding: 0 24px; }
.toc { position: sticky; top: 72px; align-self: start; max-height: calc(100vh - 90px); overflow-y: auto; padding: 32px 0; }
.toc-title { font-size: .75rem; font-weight: 600; text-transform: uppercase; letter-spacing: .08em; color: var(--ink-3); margin-bottom: 10px; }
.toc ol { list-style: none; margin: 0; padding: 0; }
.toc a { display: flex; gap: 10px; padding: 6px 10px; border-radius: var(--r-sm); color: var(--ink-2); text-decoration: none; font-size: .875rem; }
.toc a span { font-family: var(--font-mono); font-size: .75rem; color: var(--ink-3); padding-top: 2px; }
.toc a:hover, .toc a.on { background: var(--accent-fill); color: var(--accent); }
main { min-width: 0; padding-bottom: 64px; }

.hero { padding: 48px 0 32px; border-bottom: 1px solid var(--line-soft); }
.eyebrow { font-size: .875rem; font-weight: 600; color: var(--accent); margin-bottom: 10px; }
.hero h1 { font-size: clamp(2rem, 4vw, 2.75rem); line-height: 1.1; margin: 0; letter-spacing: -.035em; }
.lead { margin: 14px 0 0; font-size: 1.125rem; line-height: 1.7; color: var(--ink-3); max-width: 70ch; }
.meta { display: grid; grid-template-columns: repeat(auto-fit, minmax(170px, 1fr)); gap: 12px; margin: 28px 0 0; }
.meta div { padding: 12px 14px; border: 1px solid var(--line); border-radius: var(--r-md); background: var(--bg-2); }
.meta dt { font-size: .75rem; color: var(--ink-3); text-transform: uppercase; letter-spacing: .06em; }
.meta dd { margin: 4px 0 0; font-weight: 500; font-size: .9375rem; overflow-wrap: anywhere; }

.section { padding: 40px 0 8px; }
.section h2 { display: flex; align-items: baseline; gap: 12px; font-size: 1.625rem; margin: 0 0 8px; }
.section h2 .num { font: 500 .875rem var(--font-mono); color: var(--accent); }
.section-lead { color: var(--ink-3); max-width: 75ch; margin-bottom: 20px; }
.prose { max-width: 78ch; }

.verdict { position: relative; padding: 22px 24px; border-radius: var(--r-lg); border: 1px solid var(--info-bd); background: var(--info-bg); margin: 8px 0 20px; overflow: hidden; }
.verdict::before { content: ""; position: absolute; inset: 0 auto 0 0; width: 5px; background: var(--info-ic); }
.verdict.sev-alta { border-color: var(--danger-bd); background: var(--danger-bg); } .verdict.sev-alta::before { background: var(--danger-ic); }
.verdict.sev-media { border-color: var(--warn-bd); background: var(--warn-bg); } .verdict.sev-media::before { background: var(--warn-ic); }
.verdict.sev-baixa { border-color: var(--tip-bd); background: var(--tip-bg); } .verdict.sev-baixa::before { background: var(--tip-ic); }
.verdict-kicker { font-size: .75rem; font-weight: 600; text-transform: uppercase; letter-spacing: .08em; color: var(--ink-2); }
.verdict-title { font: 600 1.375rem/1.35 var(--font-head); margin-top: 6px; }

.kpis { display: grid; grid-template-columns: repeat(auto-fit, minmax(190px, 1fr)); gap: 12px; margin: 22px 0; }
.kpi { padding: 16px 18px; border: 1px solid var(--line); border-radius: var(--r-lg); background: var(--bg-2); }
.kpi-label { font-size: .75rem; text-transform: uppercase; letter-spacing: .06em; color: var(--ink-3); }
.kpi-value { font: 700 2rem/1.2 var(--font-head); margin-top: 4px; }
.kpi-value.small { font-size: 1.0625rem; font-weight: 600; line-height: 1.4; }
.kpi-text { margin-top: 6px; font-size: .9375rem; line-height: 1.5; color: var(--ink-2); }
.kpi-foot { font-size: .8125rem; color: var(--ink-3); margin-top: 6px; }
.bar { display: flex; gap: 3px; height: 8px; margin-top: 10px; border-radius: 99px; overflow: hidden; background: var(--fill); }
.seg { display: block; min-width: 8px; }
.seg.sev-alta, .dot.sev-alta { background: var(--danger-ic); }
.seg.sev-media, .dot.sev-media { background: var(--warn-ic); }
.seg.sev-baixa, .dot.sev-baixa { background: var(--info-ic); }
.dot { display: inline-block; width: 8px; height: 8px; border-radius: 50%; margin-right: 4px; }
.highlights { list-style: none; padding: 0; display: grid; gap: 8px; }
.highlights li { position: relative; padding: 10px 14px 10px 36px; border: 1px solid var(--line-soft); border-radius: var(--r-md); }
.highlights li::before { content: "→"; position: absolute; left: 14px; color: var(--accent); font-weight: 600; }

.solid-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(165px, 1fr)); gap: 10px; }
.solid { display: flex; gap: 12px; align-items: center; padding: 12px 14px; border-radius: var(--r-md); border: 1px solid var(--line); }
.solid-letter { display: grid; place-items: center; flex: none; width: 36px; height: 36px; border-radius: 10px; font: 700 1.125rem var(--font-head); background: var(--fill); }
.solid.sev-alta .solid-letter { background: var(--danger-bg); color: var(--danger-ic); border: 1px solid var(--danger-bd); }
.solid.sev-media .solid-letter { background: var(--warn-bg); color: var(--warn-ic); border: 1px solid var(--warn-bd); }
.solid.sev-baixa .solid-letter { background: var(--info-bg); color: var(--info-ic); border: 1px solid var(--info-bd); }
.solid.ok .solid-letter { background: var(--tip-bg); color: var(--tip-ic); border: 1px solid var(--tip-bd); }
.solid-name { font-weight: 600; font-size: .9375rem; }
.solid-refs { font-size: .8125rem; color: var(--ink-3); }

.table-wrap { overflow-x: auto; margin: 12px 0 20px; border: 1px solid var(--line); border-radius: var(--r-lg); }
table { width: 100%; border-collapse: collapse; font-size: .875rem; line-height: 1.55; }
th { text-align: left; font-weight: 600; padding: 10px 14px; background: var(--bg-2); border-bottom: 1px solid var(--line); white-space: nowrap; }
td { padding: 10px 14px; border-bottom: 1px solid var(--line-soft); vertical-align: top; }
tr:last-child td { border-bottom: 0; }
td.num, th.num { text-align: right; font-family: var(--font-mono); }
.elements ul.resp { margin: 0; padding-left: 18px; }
.elements ul.resp li { margin-bottom: 4px; }
code.strong { font-weight: 600; }
.grid-2 { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 14px; margin: 14px 0; }
.card { padding: 16px 18px; border: 1px solid var(--line); border-radius: var(--r-lg); }
.card h3 { margin-top: 0; font-size: 1rem; }

.pill { display: inline-flex; align-items: center; gap: 4px; padding: 2px 9px; margin: 2px 4px 2px 0; border-radius: 99px; font-size: .75rem; font-weight: 500; border: 1px solid var(--line); color: var(--ink-2); background: var(--bg); white-space: nowrap; }
.pill.sev-alta, .pill.warn { background: var(--danger-bg); border-color: var(--danger-bd); color: var(--danger-ic); }
.pill.warn { background: var(--warn-bg); border-color: var(--warn-bd); color: var(--warn-ic); }
.pill.sev-media { background: var(--warn-bg); border-color: var(--warn-bd); color: var(--warn-ic); }
.pill.sev-baixa { background: var(--info-bg); border-color: var(--info-bd); color: var(--info-ic); }
.pill.principle { background: var(--accent-fill); border-color: transparent; color: var(--accent); }
.pill.effect { font-family: var(--font-mono); font-size: .6875rem; }
.pill.actor { margin-left: 8px; background: var(--fill); border-color: transparent; }
.pill.lvl-alto { background: var(--tip-bg); border-color: var(--tip-bd); color: var(--tip-ic); }
.pill.lvl-medio { background: var(--info-bg); border-color: var(--info-bd); color: var(--info-ic); }
.ref { display: inline-block; padding: 0 7px; margin: 0 2px; border-radius: 6px; font: 600 .75rem/1.6 var(--font-mono); text-decoration: none; border: 1px solid var(--line); color: var(--ink-2); background: var(--bg); }
.ref.sev-alta { color: var(--danger-ic); border-color: var(--danger-bd); background: var(--danger-bg); }
.ref.sev-media { color: var(--warn-ic); border-color: var(--warn-bd); background: var(--warn-bg); }
.ref.sev-baixa { color: var(--info-ic); border-color: var(--info-bd); background: var(--info-bg); }
.ref.rec { color: var(--accent); border-color: transparent; background: var(--accent-fill); }

.stepper { list-style: none; margin: 16px 0 0; padding: 0; position: relative; }
.step { position: relative; display: grid; grid-template-columns: 40px minmax(0, 1fr); gap: 16px; padding-bottom: 18px; }
.step::before { content: ""; position: absolute; left: 19px; top: 40px; bottom: 0; width: 2px; background: var(--line); }
.step:last-child::before { display: none; }
.step-n { display: grid; place-items: center; width: 40px; height: 40px; border-radius: 50%; background: var(--primary); color: var(--bg); font: 600 .9375rem var(--font-head); }
.step-body { padding: 10px 16px 12px; border: 1px solid var(--line); border-radius: var(--r-lg); background: var(--bg); }
.step-head { display: flex; flex-wrap: wrap; align-items: baseline; justify-content: space-between; gap: 6px 12px; }
.step-title { font: 600 1rem var(--font-head); }
code.where { font-size: .75rem; }
.step-desc { color: var(--ink-2); font-size: .9375rem; margin-top: 4px; }
.step-io { font-size: .8125rem; color: var(--ink-3); margin-top: 6px; }
.arrow { color: var(--accent); font-weight: 600; margin: 0 4px; }
.step-tags { display: flex; flex-wrap: wrap; align-items: center; gap: 4px; margin-top: 8px; }
.step-tags .refs { margin-left: auto; }

.filters { display: flex; flex-wrap: wrap; gap: 8px; margin: 4px 0 18px; }
.chip { font: 500 .8125rem var(--font-body); padding: 6px 12px; border-radius: 99px; border: 1px solid var(--line); background: var(--bg); color: var(--ink-2); cursor: pointer; }
.chip span { color: var(--ink-3); margin-left: 4px; }
.chip.on { background: var(--primary); color: var(--bg); border-color: var(--primary); }
.chip.on span { color: inherit; opacity: .7; }
.findings, .recs { display: grid; gap: 18px; }
.finding, .rec-card { border: 1px solid var(--line); border-radius: var(--r-lg); padding: 18px 20px; background: var(--bg); scroll-margin-top: 80px; }
.finding:target, .rec-card:target { box-shadow: 0 0 0 3px var(--accent-fill); border-color: var(--accent); }
.bug-row { scroll-margin-top: 80px; }
.bug-row:target td { background: var(--accent-fill); }
.finding-head, .rec-head { display: flex; align-items: flex-start; gap: 12px; }
.finding-head h3, .rec-head h3 { flex: 1; margin: 2px 0 0; font-size: 1.125rem; }
.id { flex: none; display: grid; place-items: center; min-width: 40px; height: 30px; padding: 0 8px; border-radius: 8px; font: 600 .8125rem var(--font-mono); }
.id.sev-alta { background: var(--danger-bg); color: var(--danger-ic); border: 1px solid var(--danger-bd); }
.id.sev-media { background: var(--warn-bg); color: var(--warn-ic); border: 1px solid var(--warn-bd); }
.id.sev-baixa { background: var(--info-bg); color: var(--info-ic); border: 1px solid var(--info-bd); }
.id.rec { background: var(--accent-fill); color: var(--accent); }
.finding-meta { margin: 10px 0 0 52px; }
.label { display: block; font-size: .6875rem; font-weight: 600; text-transform: uppercase; letter-spacing: .08em; color: var(--ink-3); margin-bottom: 4px; }
.signal { margin: 14px 0; padding: 10px 14px; border-left: 3px solid var(--accent); background: var(--accent-fill); border-radius: 0 var(--r-sm) var(--r-sm) 0; font-size: .9375rem; }
.impact { margin-top: 12px; }
.finding-foot { display: flex; align-items: baseline; gap: 10px; padding-top: 12px; margin-top: 4px; border-top: 1px dashed var(--line); }
.finding-foot .label { display: inline; margin: 0; }
.finding[hidden] { display: none; }

.code { margin: 14px 0; border: 1px solid var(--line); border-radius: var(--r-lg); background: var(--fill); padding: 2px; }
.code-head { display: flex; align-items: center; justify-content: space-between; gap: 12px; min-height: 34px; padding: 0 6px 0 12px; font-size: .75rem; color: var(--ink-3); }
.code-title { font-weight: 500; color: var(--ink-2); }
.code-title code { font-size: .75rem; }
.copy { font: 500 .6875rem var(--font-body); color: var(--ink-3); background: transparent; border: 1px solid var(--line); border-radius: 8px; padding: 3px 8px; cursor: pointer; }
.copy:hover { color: var(--ink); }
.code-body { border-radius: 14px; background: var(--code-bg); overflow: hidden; }
.code pre { margin: 0; padding: 12px 0; overflow-x: auto; font: 400 .8125rem/1.6 var(--font-mono); color: var(--code-ink); tab-size: 4; }
.code pre code { background: none; border: 0; padding: 0; font-size: inherit; display: block; min-width: max-content; }
.ln { display: block; padding: 0 16px; border-left: 3px solid transparent; }
.numbered .ln { padding-left: 0; }
.ln .n { display: inline-block; width: 3.4em; padding-right: 1.2em; text-align: right; color: var(--t-c); opacity: .65; user-select: none; }
.ln.hl { background: var(--hl); border-left-color: var(--hl-bd); }
.lc { white-space: pre; }
.code-note { padding: 8px 12px 6px; font-size: .8125rem; color: var(--ink-2); }
.t-c { color: var(--t-c); font-style: italic; } .t-s { color: var(--t-s); } .t-k { color: var(--t-k); } .t-n { color: var(--t-n); } .t-f { color: var(--t-f); }

.matrix-wrap { display: grid; grid-template-columns: 80px minmax(0, 1fr); gap: 6px; margin: 40px 0 28px; }
.matrix-y { display: grid; grid-template-rows: repeat(3, minmax(64px, auto)); align-items: center; font-size: .75rem; color: var(--ink-3); position: relative; }
.matrix-y .axis-title { position: absolute; top: -22px; left: 0; font-weight: 600; text-transform: uppercase; letter-spacing: .06em; }
.matrix { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); grid-template-rows: repeat(3, minmax(64px, auto)); gap: 6px; }
.cell { padding: 8px; border-radius: var(--r-sm); background: var(--bg-2); border: 1px solid var(--line-soft); display: flex; flex-wrap: wrap; gap: 6px; align-content: flex-start; }
.cell.quick { background: var(--tip-bg); border-color: var(--tip-bd); }
.matrix-x { grid-column: 1 / -1; display: grid; grid-template-columns: 80px repeat(3, minmax(0, 1fr)); gap: 6px; font-size: .75rem; color: var(--ink-3); text-align: center; }
.matrix-caption { grid-column: 1 / -1; font-size: .8125rem; color: var(--ink-3); }
.mchip { font-size: .75rem; padding: 3px 8px; border-radius: 8px; background: var(--bg); border: 1px solid var(--line); color: var(--ink); text-decoration: none; }
.mchip b { font-family: var(--font-mono); color: var(--accent); margin-right: 2px; }

.rec-titles { flex: 1; }
.rec-pattern { display: flex; flex-wrap: wrap; gap: 8px; align-items: baseline; margin-top: 4px; font-size: .875rem; }
.pattern-name { font-weight: 600; color: var(--accent); }
.rec-badges { display: flex; flex-wrap: wrap; justify-content: flex-end; max-width: 220px; }
.rec-grid { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1.6fr); gap: 4px 28px; }
.quicktest { list-style: none; padding: 0; display: grid; gap: 8px; }
.quicktest li { display: flex; gap: 12px; padding: 10px 12px; border-radius: var(--r-md); background: var(--bg-2); border: 1px solid var(--line-soft); }
.quicktest .mark { flex: none; display: grid; place-items: center; width: 22px; height: 22px; border-radius: 50%; font-size: .75rem; font-weight: 700; }
.quicktest .yes .mark { background: var(--tip-bg); color: var(--tip-ic); border: 1px solid var(--tip-bd); }
.quicktest .no .mark { background: var(--danger-bg); color: var(--danger-ic); border: 1px solid var(--danger-bd); }
.quicktest .q { font-weight: 600; font-size: .875rem; }
.quicktest .a { font-size: .875rem; color: var(--ink-2); }
.callout { margin: 16px 0; padding: 14px 18px; border-radius: var(--r-lg); border: 1px solid var(--info-bd); background: var(--info-bg); font-size: .9375rem; }
.callout p:last-child, .callout ul:last-child { margin-bottom: 0; }
.callout-title { font-weight: 600; font-size: .8125rem; text-transform: uppercase; letter-spacing: .06em; margin-bottom: 6px; color: var(--info-ic); }
.callout.warn { border-color: var(--warn-bd); background: var(--warn-bg); } .callout.warn .callout-title { color: var(--warn-ic); }
.callout.tip { border-color: var(--tip-bd); background: var(--tip-bg); } .callout.tip .callout-title { color: var(--tip-ic); }
.callout.danger { border-color: var(--danger-bd); background: var(--danger-bg); } .callout.danger .callout-title { color: var(--danger-ic); }
.rec-links { font-size: .8125rem; color: var(--ink-3); margin-top: 8px; }

.roadmap { list-style: none; padding: 0; margin: 12px 0 0; counter-reset: road; }
.road-step { display: grid; grid-template-columns: 44px minmax(0, 1fr); gap: 14px; position: relative; padding-bottom: 16px; }
.road-step::before { content: ""; position: absolute; left: 21px; top: 44px; bottom: 0; width: 2px; background: repeating-linear-gradient(var(--line) 0 6px, transparent 6px 10px); }
.road-step:last-child::before { display: none; }
.road-n { display: grid; place-items: center; width: 44px; height: 44px; border-radius: 12px; border: 1.5px solid var(--accent); color: var(--accent); font: 700 1rem var(--font-head); background: var(--accent-fill); }
.road-body { padding: 10px 16px; border: 1px solid var(--line); border-radius: var(--r-lg); }
.road-head { display: flex; flex-wrap: wrap; align-items: center; gap: 6px 8px; margin-bottom: 6px; }
.road-head strong { margin-right: auto; font-family: var(--font-head); }

.gloss-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 12px; }
.gloss { padding: 16px; border: 1px solid var(--line); border-radius: var(--r-lg); }
.gloss-type { font-size: .6875rem; text-transform: uppercase; letter-spacing: .08em; color: var(--ink-3); }
.gloss-name { font: 600 1.0625rem var(--font-head); margin: 2px 0 8px; }
.gloss p { font-size: .875rem; color: var(--ink-2); }
.gloss-links { font-size: .8125rem; }
.foot { margin-top: 48px; padding-top: 20px; border-top: 1px solid var(--line-soft); font-size: .8125rem; color: var(--ink-3); }

@media (max-width: 960px) {
  .layout { grid-template-columns: minmax(0, 1fr); gap: 0; padding: 0 16px; }
  .toc { display: none; }
  .rec-grid { grid-template-columns: minmax(0, 1fr); }
  .rec-head { flex-wrap: wrap; } .rec-badges { justify-content: flex-start; max-width: none; }
  .finding-meta { margin-left: 0; }
  .topbar { padding: 10px 16px; }
}
@media (max-width: 560px) {
  .matrix-wrap { grid-template-columns: 52px minmax(0, 1fr); }
  .matrix-x { grid-template-columns: 52px repeat(3, minmax(0, 1fr)); }
  .step { grid-template-columns: 32px minmax(0, 1fr); gap: 10px; } .step-n { width: 32px; height: 32px; } .step::before { left: 15px; top: 32px; }
}
@media print {
  .topbar, .toc, .filters, .copy { display: none !important; }
  .layout { display: block; max-width: none; padding: 0; }
  .finding[hidden] { display: block !important; }
  .section { break-inside: auto; } .finding, .rec-card, .step, .road-step { break-inside: avoid; }
  body { font-size: 11pt; }
}
"""

JS = """
(function () {
  var root = document.documentElement;
  document.getElementById('theme').addEventListener('click', function () {
    var atual = root.dataset.theme || (matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
    var novo = atual === 'dark' ? 'light' : 'dark';
    root.dataset.theme = novo;
    try { localStorage.setItem('devmap-theme', novo); } catch (e) {}
  });
  document.getElementById('print').addEventListener('click', function () { window.print(); });

  var chips = document.querySelectorAll('.filters .chip');
  chips.forEach(function (chip) {
    chip.addEventListener('click', function () {
      chips.forEach(function (c) { c.classList.toggle('on', c === chip); });
      var f = chip.dataset.filter;
      document.querySelectorAll('.finding').forEach(function (el) {
        el.hidden = !(f === 'todos' || el.dataset.sev === f);
      });
    });
  });

  document.querySelectorAll('.copy').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var raw = btn.closest('.code').querySelector('.raw');
      var texto = raw ? raw.value : '';
      var pronto = function () { btn.textContent = 'Copiado'; setTimeout(function () { btn.textContent = 'Copiar'; }, 1400); };
      if (navigator.clipboard) navigator.clipboard.writeText(texto).then(pronto, function () {});
    });
  });

  var links = {};
  document.querySelectorAll('.toc a').forEach(function (a) { links[a.getAttribute('href').slice(1)] = a; });
  if ('IntersectionObserver' in window) {
    var obs = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting && links[e.target.id]) {
          Object.keys(links).forEach(function (k) { links[k].classList.toggle('on', k === e.target.id); });
        }
      });
    }, { rootMargin: '-20% 0px -70% 0px' });
    document.querySelectorAll('main .section').forEach(function (s) { obs.observe(s); });
  }
})();
"""


# ── principal ─────────────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("json", type=Path, help="relatorio.json")
    parser.add_argument("--raiz", type=Path, default=Path.cwd(), help="raiz do projeto analisado (padrão: pasta atual)")
    parser.add_argument("--saida", type=Path, help="HTML de saída (padrão: relatorio.html ao lado do JSON)")
    args = parser.parse_args()
    for fluxo in (sys.stdout, sys.stderr):
        try:
            fluxo.reconfigure(encoding="utf-8")  # console do Windows (cp1252) quebra os acentos
        except (AttributeError, ValueError):
            pass

    try:
        dados = json.loads(args.json.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as erro:
        print(f"ERRO: não foi possível ler {args.json}: {erro}", file=sys.stderr)
        return 1

    catalogo = carregar_catalogo()
    if not catalogo:
        print(f"AVISO: referências não encontradas em {REFERENCIAS}; o glossário vai sair vazio", file=sys.stderr)

    v = Validacao()
    validar(dados, args.raiz, catalogo, v)
    for aviso in v.avisos:
        print(f"AVISO: {aviso}")
    if v.erros:
        for erro in v.erros:
            print(f"ERRO: {erro}")
        print(f"{len(v.erros)} erro(s). O HTML não foi gerado.")
        return 1

    saida = args.saida or args.json.with_name("relatorio.html")
    saida.write_text(render(dados, args.raiz, args.json.resolve().parent, catalogo), encoding="utf-8", newline="\n")
    print(f"OK: {saida} ({len(dados['achados'])} achados, {len(dados['recomendacoes'])} recomendações)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
