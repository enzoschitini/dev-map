"""Gera as referências da skill python-pattern a partir das páginas de pages/clean-code.

Converte cada página HTML em Markdown, na mesma árvore de pastas, e monta
references/sinais.md: o índice de sinais usado no diagnóstico (as tabelas
"Como reconhecer" dos princípios SOLID e "Quando usar" + "Um teste rápido" de
cada pattern).

O texto não é reescrito: a fonte da verdade continua sendo o site. Rode de novo
sempre que uma página mudar.

Uso, a partir da raiz do repositório:

    py .claude/skills/python-pattern/scripts/sync_references.py
    py .claude/skills/python-pattern/scripts/sync_references.py --com-typescript
"""

from __future__ import annotations

import argparse
import posixpath
import re
import shutil
import sys
from html.parser import HTMLParser
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = SKILL_DIR.parents[2]
FONTE_PADRAO = REPO_ROOT / "pages" / "clean-code"
DESTINO_PADRAO = SKILL_DIR / "references"

GRUPOS = [("criacionais", "Criacionais"), ("estruturais", "Estruturais"), ("comportamentais", "Comportamentais")]
SOLID = [
    ("single-responsibility", "S"),
    ("open-closed", "O"),
    ("liskov-substitution", "L"),
    ("interface-segregation", "I"),
    ("dependency-inversion", "D"),
]
CALLOUTS = {"tip": "Dica", "note": "Nota", "warn": "Cuidado", "danger": "Perigo"}
VOID = {"br", "img", "hr", "meta", "link", "input", "source"}


# ── árvore HTML mínima ────────────────────────────────────────────────────────

class Node:
    def __init__(self, tag: str, attrs: list[tuple[str, str | None]], parent: Node | None):
        self.tag = tag
        self.attrs = {k: (v or "") for k, v in attrs}
        self.children: list[Node | str] = []
        self.parent = parent

    @property
    def classes(self) -> list[str]:
        return self.attrs.get("class", "").split()

    def find_all(self, tag: str | None = None, cls: str | None = None) -> list[Node]:
        achados = []
        for filho in self.children:
            if isinstance(filho, Node):
                if (tag is None or filho.tag == tag) and (cls is None or cls in filho.classes):
                    achados.append(filho)
                achados.extend(filho.find_all(tag, cls))
        return achados

    def find(self, tag: str | None = None, cls: str | None = None) -> Node | None:
        achados = self.find_all(tag, cls)
        return achados[0] if achados else None


class TreeBuilder(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.root = Node("root", [], None)
        self.atual = self.root

    def handle_starttag(self, tag, attrs):
        no = Node(tag, attrs, self.atual)
        self.atual.children.append(no)
        if tag not in VOID:
            self.atual = no

    def handle_endtag(self, tag):
        no = self.atual
        while no is not None and no.tag != tag:
            no = no.parent
        if no is not None and no.parent is not None:
            self.atual = no.parent

    def handle_data(self, data):
        self.atual.children.append(data)


def parse(html: str) -> Node:
    builder = TreeBuilder()
    builder.feed(html)
    builder.close()
    return builder.root


def texto(no: Node | str) -> str:
    if isinstance(no, str):
        return no
    return "".join(texto(f) for f in no.children)


# ── conversão para Markdown ───────────────────────────────────────────────────

class Conversor:
    """Converte nós de uma página para Markdown.

    `origem` é o .md da página relativo a references/; `saida` é a pasta do arquivo
    em que o trecho vai ser escrito. Os links são reescritos de uma para a outra.
    """

    def __init__(self, origem: str, saida: str, linguagens: set[str]):
        self.origem = origem
        self.base = posixpath.dirname(origem)
        self.saida = saida
        self.linguagens = linguagens

    def href(self, href: str) -> str:
        if re.match(r"^[a-z]+:", href):
            return href
        if href.startswith("#"):
            # Âncora da própria página: só continua válida se o trecho for escrito nela.
            if self.saida == self.base:
                return href
            return posixpath.relpath(self.origem, self.saida or ".") + href
        caminho, _, ancora = href.partition("#")
        if not caminho.endswith(".html"):
            return href
        alvo = posixpath.normpath(posixpath.join(self.base, caminho[: -len(".html")] + ".md"))
        relativo = posixpath.relpath(alvo, self.saida or ".")
        return relativo + (f"#{ancora}" if ancora else "")

    def inline(self, no: Node | str) -> str:
        if isinstance(no, str):
            return re.sub(r"\s+", " ", no)
        partes = []
        for filho in no.children:
            if isinstance(filho, str):
                partes.append(re.sub(r"\s+", " ", filho))
            elif filho.tag == "code":
                conteudo = re.sub(r"\s+", " ", texto(filho))
                cerca = "``" if "`" in conteudo else "`"
                espaco = " " if cerca == "``" else ""
                partes.append(f"{cerca}{espaco}{conteudo}{espaco}{cerca}")
            elif filho.tag in ("strong", "b"):
                partes.append(f"**{self.inline(filho).strip()}**")
            elif filho.tag in ("em", "i"):
                partes.append(f"*{self.inline(filho).strip()}*")
            elif filho.tag == "a":
                partes.append(f"[{self.inline(filho).strip()}]({self.href(filho.attrs.get('href', ''))})")
            elif filho.tag == "br":
                partes.append(" ")
            else:
                partes.append(self.inline(filho))
        return "".join(partes)

    def blocos(self, no: Node) -> list[str]:
        saida: list[str] = []
        for filho in no.children:
            if isinstance(filho, str):
                if filho.strip():
                    saida.append(re.sub(r"\s+", " ", filho).strip())
                continue
            tag, classes = filho.tag, filho.classes
            if tag in ("h2", "h3", "h4"):
                nivel = "#" * int(tag[1])
                ancora = filho.attrs.get("id")
                linha = f"{nivel} {self.inline(filho).strip()}"
                saida.append(f'<a id="{ancora}"></a>\n{linha}' if ancora else linha)
            elif tag == "p":
                saida.append(self.inline(filho).strip())
            elif tag == "div" and "code" in classes:
                bloco = self.codigo(filho)
                if bloco:
                    saida.append(bloco)
            elif tag == "pre":
                saida.append(self.cerca(texto(filho), adivinhar_linguagem(texto(filho))))
            elif tag == "div" and "callout" in classes:
                saida.append(self.callout(filho))
            elif tag == "table":
                saida.append(self.tabela(filho))
            elif tag in ("ul", "ol"):
                saida.append(self.lista(filho))
            elif tag in ("button", "script", "style"):
                continue
            else:
                saida.extend(self.blocos(filho))
        return saida

    def cerca(self, codigo: str, linguagem: str) -> str:
        codigo = codigo.strip("\n")
        cerca = "````" if "```" in codigo else "```"
        return f"{cerca}{linguagem}\n{codigo}\n{cerca}"

    def codigo(self, no: Node) -> str:
        titulo_no = no.find(cls="code-title")
        titulo = re.sub(r"\s+", " ", texto(titulo_no)).strip() if titulo_no else ""
        abas = [texto(b).strip() for b in no.find_all("button", "code-tab")]
        pres = no.find_all("pre")
        if abas:
            pares = [(aba.lower(), pre) for aba, pre in zip(abas, pres) if aba.lower() in self.linguagens]
        else:
            pares = [(adivinhar_linguagem(texto(pre)), pre) for pre in pres]
        if not pares:
            return ""
        partes = [f"**{titulo}**"] if titulo else []
        partes += [self.cerca(texto(pre), linguagem) for linguagem, pre in pares]
        return "\n\n".join(partes)

    def callout(self, no: Node) -> str:
        rotulo = CALLOUTS.get(no.attrs.get("data-kind", ""), "Nota")
        corpo = "\n\n".join(self.blocos(no))
        corpo = f"**{rotulo}.** {corpo}"
        return "\n".join(f"> {linha}" if linha else ">" for linha in corpo.split("\n"))

    def tabela(self, no: Node) -> str:
        linhas = []
        for tr in no.find_all("tr"):
            celulas = [c for c in tr.children if isinstance(c, Node) and c.tag in ("th", "td")]
            linhas.append([self.inline(c).strip().replace("|", "\\|") for c in celulas])
        if not linhas:
            return ""
        largura = max(len(l) for l in linhas)
        linhas = [l + [""] * (largura - len(l)) for l in linhas]
        md = ["| " + " | ".join(linhas[0]) + " |", "|" + "---|" * largura]
        md += ["| " + " | ".join(l) + " |" for l in linhas[1:]]
        return "\n".join(md)

    def lista(self, no: Node, recuo: str = "") -> str:
        itens = []
        numero = 1
        for li in no.children:
            if not isinstance(li, Node) or li.tag != "li":
                continue
            marcador = f"{numero}." if no.tag == "ol" else "-"
            numero += 1
            sublistas = [f for f in li.children if isinstance(f, Node) and f.tag in ("ul", "ol")]
            corpo = Node("li", [], None)
            corpo.children = [f for f in li.children if f not in sublistas]
            itens.append(f"{recuo}{marcador} {self.inline(corpo).strip()}")
            for sub in sublistas:
                itens.append(self.lista(sub, recuo + "   "))
        return "\n".join(itens)


def adivinhar_linguagem(codigo: str) -> str:
    python = len(re.findall(
        r"^\s*(def |class \w+.*:\s*$|elif |try:|except\b|from \w[\w.]* import |import \w)"
        r"|\bself\b|\bNone\b|\bTrue\b|\bFalse\b|\bf\"|(^|\s)# ",
        codigo, re.M,
    ))
    typescript = len(re.findall(
        r"\b(const|let|interface|function|export|readonly)\b|=>|;\s*$|\bnull\b|\bundefined\b|(^|\s)// ",
        codigo, re.M,
    ))
    if python > typescript:
        return "python"
    if typescript > python:
        return "typescript"
    return ""


# ── páginas ───────────────────────────────────────────────────────────────────

class Pagina:
    def __init__(self, arquivo: Path, fonte: Path, linguagens: set[str]):
        self.arquivo = arquivo
        self.relativo = arquivo.relative_to(fonte).as_posix()
        html = arquivo.read_text(encoding="utf-8")
        main = re.search(r"<main\b[^>]*>(.*)</main>", html, re.S)
        if not main:
            raise ValueError(f"{self.relativo}: <main> não encontrado")
        self.raiz = parse(main.group(1))
        self.prose = self.raiz.find("div", "prose")
        if self.prose is None:
            raise ValueError(f"{self.relativo}: .prose não encontrado")
        self.eyebrow = self._texto_de(self.raiz.find("div", "eyebrow"))
        self.titulo = self._texto_de(self.raiz.find("h1"))
        self.lead_no = self.raiz.find("p", "lead")
        self.base = posixpath.dirname(self.relativo)
        self.linguagens = linguagens

    @staticmethod
    def _texto_de(no: Node | None) -> str:
        return re.sub(r"\s+", " ", texto(no)).strip() if no else ""

    @property
    def nome(self) -> str:
        # Páginas de pattern têm h1 "Explicação"/"Uso" e o nome no fim do eyebrow;
        # as outras têm o nome no h1 (o eyebrow pode ter "/" no nome, como "Open/Closed").
        if "/" in self.relativo:
            return self.eyebrow.rsplit(" / ", 1)[-1].strip() or self.titulo
        return self.titulo

    def conversor(self, saida: str) -> Conversor:
        return Conversor(self.relativo[: -len(".html")] + ".md", saida, self.linguagens)

    def markdown(self) -> str:
        conv = self.conversor(self.base)
        cabecalho = self.titulo if self.titulo == self.nome else f"{self.nome} — {self.titulo}"
        partes = [
            f"<!-- Gerado de pages/clean-code/{self.relativo} por scripts/sync_references.py. "
            "Não edite aqui: edite a página e rode o script. -->",
            f"# {cabecalho}",
            f"*{self.eyebrow}*",
        ]
        if self.lead_no is not None:
            partes.append(conv.inline(self.lead_no).strip())
        partes += conv.blocos(self.prose)
        return "\n\n".join(partes) + "\n"

    def secao(self, ancora: str) -> list[Node | str]:
        """Nós entre o título com esse id e o próximo título de mesmo nível ou acima."""
        nos = self.prose.children
        for i, no in enumerate(nos):
            if isinstance(no, Node) and no.attrs.get("id") == ancora:
                nivel = int(no.tag[1])
                fim = len(nos)
                for j in range(i + 1, len(nos)):
                    outro = nos[j]
                    if isinstance(outro, Node) and outro.tag in ("h2", "h3") and int(outro.tag[1]) <= nivel:
                        fim = j
                        break
                return nos[i + 1 : fim]
        return []

    def primeiro(self, ancora: str, tag: str) -> Node | None:
        for no in self.secao(ancora):
            if isinstance(no, Node):
                if no.tag == tag:
                    return no
                achado = no.find(tag)
                if achado is not None:
                    return achado
        return None

    def primeiro_paragrafo(self, ancora: str) -> Node | None:
        for no in self.secao(ancora):
            if isinstance(no, Node) and no.tag == "p":
                return no
        return None


# ── índice de sinais ──────────────────────────────────────────────────────────

def frequencias(paginas: dict[str, Pagina]) -> dict[str, str]:
    """Lê a tabela de patterns-frequencia: nome do pattern → nível de uso."""
    pagina = paginas.get("patterns-frequencia.html")
    if pagina is None:
        return {}
    tabela = pagina.primeiro("tabela", "table")
    if tabela is None:
        return {}
    cabecalho = [texto(c).strip().lower() for c in tabela.find_all("th")]
    coluna = next((i for i, c in enumerate(cabecalho) if "frequ" in c), None)
    nome = next((i for i, c in enumerate(cabecalho) if "pattern" in c or "padr" in c), None)
    if coluna is None or nome is None:
        return {}
    niveis = {}
    for tr in tabela.find_all("tr"):
        celulas = [c for c in tr.children if isinstance(c, Node) and c.tag == "td"]
        if len(celulas) > max(coluna, nome):
            niveis[re.sub(r"\s+", " ", texto(celulas[nome])).strip()] = re.sub(r"\s+", " ", texto(celulas[coluna])).strip().lower()
    return niveis


def sinais(paginas: dict[str, Pagina]) -> str:
    md = [
        "<!-- Gerado por scripts/sync_references.py a partir de pages/clean-code. Não edite aqui. -->",
        "# Índice de sinais",
        "Use este índice na fase de diagnóstico: procure no código analisado os sinais da coluna "
        "\"Como reconhecer\". Um sinal encontrado é uma **hipótese**, não uma decisão: antes de "
        "planejar, abra a página do princípio ou do pattern e confira \"Quando não usar\" / "
        "\"Quando não aplicar\" e o \"Teste rápido\".",
        "## Sumário",
        "- [SOLID](#solid)\n" + "\n".join(f"- [{rotulo}](#{pasta})" for pasta, rotulo in GRUPOS),
        '<a id="solid"></a>\n## SOLID',
    ]
    for slug, letra in SOLID:
        pagina = paginas.get(f"{slug}.html")
        if pagina is None:
            continue
        conv = pagina.conversor("")
        md.append(f"### {letra} — [{pagina.nome}]({slug}.md)")
        if pagina.lead_no is not None:
            md.append(conv.inline(pagina.lead_no).strip())
        tabela = pagina.primeiro("como-reconhecer", "table")
        if tabela is not None:
            md.append(conv.tabela(tabela))
        md.append(f"Antes de aplicar: [Quando não aplicar]({slug}.md#quando-nao-aplicar).")

    niveis = frequencias(paginas)
    for pasta, rotulo in GRUPOS:
        md.append(f'<a id="{pasta}"></a>\n## {rotulo}')
        explicacoes = sorted(
            (p for r, p in paginas.items() if r.startswith(f"{pasta}/") and r.endswith("/explicacao.html")),
            key=lambda p: p.nome,
        )
        for pagina in explicacoes:
            conv = pagina.conversor("")
            nivel = niveis.get(pagina.nome)
            md.append(f"### [{pagina.nome}]({pagina.base}/explicacao.md)" + (f" · uso: {nivel}" if nivel else ""))
            if pagina.lead_no is not None:
                md.append(conv.inline(pagina.lead_no).strip())
            regra = pagina.primeiro_paragrafo("quando-usar")
            if regra is not None:
                md.append(f"**Regra.** {conv.inline(regra).strip()}")
            tabela = pagina.primeiro("quando-usar", "table")
            if tabela is not None:
                md.append(conv.tabela(tabela))
            teste = pagina.primeiro("teste-rapido", "ol")
            if teste is not None:
                md.append("**Teste rápido.**\n\n" + conv.lista(teste))
            md.append(
                f"Antes de aplicar: [Quando não usar]({pagina.base}/explicacao.md#quando-nao-usar) · "
                f"[Parecidos]({pagina.base}/explicacao.md#parecidos) · [Exemplos]({pagina.base}/uso.md)."
            )
    return "\n\n".join(md) + "\n"


# ── principal ─────────────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--fonte", type=Path, default=FONTE_PADRAO, help="pasta pages/clean-code")
    parser.add_argument("--destino", type=Path, default=DESTINO_PADRAO, help="pasta references da skill")
    parser.add_argument(
        "--com-typescript",
        action="store_true",
        help="mantém a aba TypeScript dos blocos com abas (por padrão só a aba Python é mantida)",
    )
    args = parser.parse_args()
    for fluxo in (sys.stdout, sys.stderr):
        try:
            fluxo.reconfigure(encoding="utf-8")  # console do Windows (cp1252) quebra os acentos
        except (AttributeError, ValueError):
            pass

    if not args.fonte.is_dir():
        print(f"fonte não encontrada: {args.fonte}", file=sys.stderr)
        return 1

    linguagens = {"python", "typescript"} if args.com_typescript else {"python"}
    paginas: dict[str, Pagina] = {}
    for arquivo in sorted(args.fonte.rglob("*.html")):
        pagina = Pagina(arquivo, args.fonte, linguagens)
        paginas[pagina.relativo] = pagina

    # Apaga só o que este script gera; os templates e outros arquivos escritos à mão ficam.
    for pasta, _ in GRUPOS:
        shutil.rmtree(args.destino / pasta, ignore_errors=True)
    for antigo in args.destino.glob("*.md"):
        if antigo.read_text(encoding="utf-8").startswith("<!-- Gerado"):
            antigo.unlink()

    for relativo, pagina in paginas.items():
        destino = args.destino / (relativo[: -len(".html")] + ".md")
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_text(pagina.markdown(), encoding="utf-8", newline="\n")

    (args.destino / "sinais.md").write_text(sinais(paginas), encoding="utf-8", newline="\n")
    print(f"{len(paginas)} páginas convertidas + sinais.md em {args.destino}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
