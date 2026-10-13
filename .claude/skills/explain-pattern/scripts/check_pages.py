#!/usr/bin/env python3
"""Confere as páginas de um design pattern geradas pela skill explain-pattern.

Uso (a partir da raiz do repositório):
    python .claude/skills/explain-pattern/scripts/check_pages.py pages/clean-code/<grupo>/<pattern>

Confere em explicacao.html e uso.html:
  - tags balanceadas (pega também um "<" sem escape dentro de <pre>)
  - id em todo h2/h3 e ids sem repetição
  - blocos .code[data-tabs] com o mesmo número de abas e de <pre>
  - data-root, data-tab e data-page coerentes com o caminho do arquivo
  - links internos: o arquivo existe e a âncora existe nele
  - as duas páginas registradas em assets/js/site.js

Sai com código 1 se encontrar algum problema.
"""
import json
import shutil
import subprocess
import sys
from html.parser import HTMLParser
from pathlib import Path

VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}
PAGES = ("explicacao.html", "uso.html")


class Page(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []
        self.errors = []
        self.ids = set()
        self.hrefs = []
        self.body = {}
        self.tabs = []        # [linha, abas, pres, profundidade]
        self.open_tabs = None

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        line = self.getpos()[0]
        if "id" in a:
            if a["id"] in self.ids:
                self.errors.append(f"linha {line}: id repetido '{a['id']}'")
            self.ids.add(a["id"])
        if tag in ("h2", "h3") and "id" not in a:
            self.errors.append(f"linha {line}: <{tag}> sem id (o índice da página precisa dele)")
        if tag == "a" and a.get("href"):
            self.hrefs.append((a["href"], line))
        if tag == "body":
            self.body = a
        cls = (a.get("class") or "").split()
        if tag == "div" and "code" in cls and "data-tabs" in a:
            self.tabs.append([line, 0, 0, len(self.stack)])
            self.open_tabs = len(self.tabs) - 1
        if self.open_tabs is not None:
            if tag == "button" and "code-tab" in cls:
                self.tabs[self.open_tabs][1] += 1
            if tag == "pre":
                self.tabs[self.open_tabs][2] += 1
        if tag not in VOID:
            self.stack.append((tag, line))

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in VOID:
            self.stack.pop()

    def handle_endtag(self, tag):
        if tag in VOID:
            return
        line = self.getpos()[0]
        if not self.stack or self.stack[-1][0] != tag:
            aberta = f"<{self.stack[-1][0]}> da linha {self.stack[-1][1]}" if self.stack else "nada"
            self.errors.append(f"linha {line}: </{tag}> fecha, mas a tag aberta é {aberta}")
            for i in range(len(self.stack) - 1, -1, -1):
                if self.stack[i][0] == tag:
                    del self.stack[i:]
                    break
            return
        self.stack.pop()
        if self.open_tabs is not None and len(self.stack) == self.tabs[self.open_tabs][3]:
            self.open_tabs = None

    def close(self):
        super().close()
        for tag, line in self.stack:
            self.errors.append(f"linha {line}: <{tag}> nunca foi fechada")
        for line, abas, pres, _ in self.tabs:
            if abas != pres:
                self.errors.append(f"linha {line}: bloco com abas tem {abas} abas e {pres} <pre>")


def parse(path):
    p = Page()
    p.feed(path.read_text(encoding="utf-8"))
    p.close()
    return p


def find_root(start):
    for d in [start, *start.parents]:
        if (d / "assets" / "js" / "site.js").is_file():
            return d
    return None


def site_pages(root, tab):
    """Lista os caminhos registrados na aba, ex.: 'estruturais/adapter/uso'."""
    node = shutil.which("node")
    if not node:
        return None
    js = (
        "global.window = {}; require(process.argv[1]);"
        "const tab = window.DEVMAP.tabs.find(t => t.id === process.argv[2]);"
        "const flat = (ns, pre) => ns.flatMap(n => n.group ? flat(n.pages, pre)"
        "  : n.folder ? flat(n.pages, pre + n.folder + '/') : [pre + n.id]);"
        "console.log(JSON.stringify(tab ? flat(tab.pages, '') : null));"
    )
    r = subprocess.run([node, "-e", js, str(root / "assets" / "js" / "site.js"), tab],
                       capture_output=True, text=True, encoding="utf-8")
    if r.returncode != 0:
        raise RuntimeError(r.stderr.strip())
    return json.loads(r.stdout)


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if len(sys.argv) != 2:
        print(__doc__)
        return 2

    folder = Path(sys.argv[1]).resolve()
    root = find_root(folder)
    if not root:
        print(f"não achei assets/js/site.js acima de {folder}")
        return 2

    rel = folder.relative_to(root).parts          # ('pages', 'clean-code', 'estruturais', 'adapter')
    if len(rel) < 3 or rel[0] != "pages":
        print(f"{folder} não está dentro de pages/<aba>/")
        return 2
    tab, inner = rel[1], "/".join(rel[2:])
    expected_root = "../" * len(rel)

    problems = []
    parsed, cache = {}, {}

    for name in PAGES:
        path = folder / name
        if not path.is_file():
            problems.append(f"{name}: arquivo não existe")
            continue
        p = parsed[name] = cache[path] = parse(path)
        problems += [f"{name}: {e}" for e in p.errors]

        b = p.body
        stem = name[:-5]
        if b.get("data-root") != expected_root:
            problems.append(f"{name}: data-root é '{b.get('data-root')}', esperado '{expected_root}'")
        if b.get("data-tab") != tab:
            problems.append(f"{name}: data-tab é '{b.get('data-tab')}', esperado '{tab}'")
        if b.get("data-page") != f"{inner}/{stem}":
            problems.append(f"{name}: data-page é '{b.get('data-page')}', esperado '{inner}/{stem}'")

    for name, p in parsed.items():
        for href, line in p.hrefs:
            if href.startswith(("http:", "https:", "mailto:", "//")):
                continue
            file_part, _, frag = href.partition("#")
            target = (folder / file_part).resolve() if file_part else folder / name
            if not target.is_file():
                problems.append(f"{name} linha {line}: link para '{href}', mas o arquivo não existe")
                continue
            if frag:
                if target not in cache:
                    cache[target] = parse(target)
                if frag not in cache[target].ids:
                    problems.append(f"{name} linha {line}: link para '{href}', mas não há id '{frag}' lá")

    if "explicacao.html" in parsed and "uso.html" in parsed:
        linked = {h.partition("#")[2] for h, _ in parsed["explicacao.html"].hrefs if h.startswith("uso.html#")}
        examples = {i for i in parsed["uso.html"].ids
                    if i not in {"main", "header", "side", "toc", "search", "como-escolhi", "fora-da-lista"}}
        for i in sorted(examples - linked):
            problems.append(f"uso.html: o exemplo '#{i}' não é citado em nenhum link da Explicação")

    try:
        registered = site_pages(root, tab)
    except Exception as e:
        problems.append(f"site.js não carregou no node: {e}")
        registered = None
    if registered is None:
        print("aviso: node não encontrado; o registro no site.js não foi conferido")
    else:
        for name in PAGES:
            key = f"{inner}/{name[:-5]}"
            n = registered.count(key)
            if n == 0:
                problems.append(f"site.js: '{key}' não está registrado na aba '{tab}'")
            elif n > 1:
                problems.append(f"site.js: '{key}' está registrado {n} vezes")

    if problems:
        print(f"{len(problems)} problema(s):")
        for p in problems:
            print("  - " + p)
        return 1
    print(f"ok: {inner} — explicacao.html e uso.html sem problemas")
    return 0


if __name__ == "__main__":
    sys.exit(main())
