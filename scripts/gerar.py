#!/usr/bin/env python3
"""Gera as páginas estáticas do currículo a partir de src/cv.html.

src/cv.html é a FONTE bilíngue: cada trecho traduzível é um elemento com a
classe `i18n` e os atributos data-pt / data-en. Este script resolve o idioma
de cada elemento e escreve páginas estáticas de verdade (sem JavaScript), com
<html lang>, título, descrição, canonical e hreflang próprios:

    index.html      português (raiz; é também o fallback se a Function falhar)
    pt/index.html   português (link do seletor quando a raiz do domínio é inglês)
    en/index.html   inglês

Uso:
    python3 scripts/gerar.py           # regrava os 3 arquivos
    python3 scripts/gerar.py --check   # falha (exit 1) se estiverem desatualizados

Só biblioteca padrão. Edite SEMPRE src/cv.html e rode o script; os arquivos
gerados são versionados porque o Cloudflare Pages publica sem etapa de build.
"""
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
FONTE = RAIZ / "src" / "cv.html"

# Domínio "dono" de cada idioma: o canonical e o hreflang apontam pra raiz dele.
SITE = {"pt": "https://bmoraes.com.br/", "en": "https://bmoraes.com/"}
DOMINIO = {"pt": "bmoraes.com.br", "en": "bmoraes.com"}

TITULO = {
    "pt": "Bruno Moraes — Desenvolvedor Backend Sênior",
    "en": "Bruno Moraes — Senior Backend Developer",
}
DESCRICAO = {
    "pt": "Currículo de Bruno Moraes — Desenvolvedor Backend Sênior, Java &amp; Spring Boot.",
    "en": "Résumé of Bruno Moraes — Senior Backend Developer, Java &amp; Spring Boot.",
}
LOCALE = {"pt": "pt_BR", "en": "en_US"}
HTML_LANG = {"pt": "pt-BR", "en": "en"}

SAIDAS = {"index.html": "pt", "pt/index.html": "pt", "en/index.html": "en"}


class _Localizador(HTMLParser):
    """Acha cada elemento `.i18n` (início da abertura, fim do fechamento) com
    os textos data-pt/data-en. Usa posições absolutas no texto original porque
    os atributos trazem `>` e `<b>` dentro de aspas."""

    def __init__(self, texto):
        super().__init__(convert_charrefs=False)
        self.texto = texto
        self.inicios = [0]
        for linha in texto.split("\n"):
            self.inicios.append(self.inicios[-1] + len(linha) + 1)
        self.achados = []  # (ini_abertura, fim_abertura, fim_fechamento, valores)
        self._aberto = None  # dict do elemento i18n em andamento

    def _pos(self):
        linha, col = self.getpos()
        return self.inicios[linha - 1] + col

    def handle_starttag(self, tag, attrs):
        ini = self._pos()
        bruto = self.get_starttag_text()
        if self._aberto is not None:
            if tag == self._aberto["tag"]:
                self._aberto["prof"] += 1
            return
        d = dict(attrs)
        if "i18n" in (d.get("class") or "").split() and "data-pt" in d and "data-en" in d:
            self._aberto = {
                "tag": tag, "prof": 1, "ini": ini, "fim_ab": ini + len(bruto),
                "pt": d["data-pt"], "en": d["data-en"],
            }

    def handle_endtag(self, tag):
        a = self._aberto
        if a is None or tag != a["tag"]:
            return
        a["prof"] -= 1
        if a["prof"] == 0:
            ini = self._pos()
            fim = self.texto.index(">", ini) + 1
            self.achados.append((a["ini"], a["fim_ab"], fim, a["pt"], a["en"], ini))
            self._aberto = None


def _escapar_e_comercial(valor):
    # O JS original fazia innerHTML = valor (já sem entidades); reescreve só os
    # "&" soltos. As tags (<b>) do valor são intencionais e ficam como estão.
    return re.sub(r"&(?![a-zA-Z]+;|#\d+;)", "&amp;", valor)


def _limpar_abertura(abertura):
    abertura = re.sub(r'\s+data-(?:pt|en)="[^"]*"', "", abertura)

    def _classe(m):
        restantes = [c for c in m.group(1).split() if c != "i18n"]
        return f' class="{" ".join(restantes)}"' if restantes else ""

    return re.sub(r'\s+class="([^"]*)"', _classe, abertura, count=1)


def _resolver_idiomas(texto, lang):
    loc = _Localizador(texto)
    loc.feed(texto)
    loc.close()
    assert loc.achados, "nenhum elemento i18n encontrado"
    partes, cursor = [], 0
    for ini, fim_ab, fim, pt, en, ini_fecha in loc.achados:
        abertura = _limpar_abertura(texto[ini:fim_ab])
        fechamento = texto[ini_fecha:fim]
        valor = _escapar_e_comercial(pt if lang == "pt" else en)
        partes.append(texto[cursor:ini])
        partes.append(abertura + valor + fechamento)
        cursor = fim
    partes.append(texto[cursor:])
    return "".join(partes)


def _trocar(texto, antigo, novo, vezes=1):
    assert texto.count(antigo) == vezes, f"esperava {vezes}x: {antigo[:60]!r} (achei {texto.count(antigo)})"
    return texto.replace(antigo, novo)


def gerar(lang):
    t = FONTE.read_text(encoding="utf-8")
    t = _resolver_idiomas(t, lang)

    t = _trocar(t, '<html lang="pt-BR">', f'<html lang="{HTML_LANG[lang]}">')
    t = _trocar(t, "<title>Bruno Moraes</title>", f"<title>{TITULO[lang]}</title>")
    desc_antiga = re.search(r'<meta name="description" content="[^"]*">', t).group(0)
    outro = "en" if lang == "pt" else "pt"
    cabecalho = "\n".join([
        f'<meta name="description" content="{DESCRICAO[lang]}">',
        f'<link rel="canonical" href="{SITE[lang]}">',
        f'<link rel="alternate" hreflang="pt-BR" href="{SITE["pt"]}">',
        f'<link rel="alternate" hreflang="en" href="{SITE["en"]}">',
        f'<link rel="alternate" hreflang="x-default" href="{SITE["en"]}">',
        '<meta property="og:type" content="profile">',
        f'<meta property="og:title" content="{TITULO[lang]}">',
        f'<meta property="og:description" content="{DESCRICAO[lang]}">',
        f'<meta property="og:url" content="{SITE[lang]}">',
        f'<meta property="og:locale" content="{LOCALE[lang]}">',
        f'<meta property="og:locale:alternate" content="{LOCALE[outro]}">',
    ])
    t = _trocar(t, desc_antiga, cabecalho)

    # Domínio exibido: o de cada idioma (o link pro "site" acompanha).
    t = _trocar(t, '<span class="mark">bmoraes.com.br</span>', f'<span class="mark">{DOMINIO[lang]}</span>')
    if lang == "en":
        t = _trocar(t, 'href="https://bmoraes.com.br"', f'href="https://{DOMINIO[lang]}"')
        t = _trocar(t, "</svg>bmoraes.com.br</a>", f"</svg>{DOMINIO[lang]}</a>")

    # Seletor de idioma: links reais (sem JS). Caminhos relativos funcionam em
    # qualquer domínio e em preview; /pt/ e /en/ existem em todos.
    def _link(alvo, rotulo, hreflang):
        ativo = ' class="active" aria-current="page"' if alvo == lang else ""
        return f'<a href="/{alvo}/" hreflang="{hreflang}"{ativo}>{rotulo}</a>'

    seletor = (
        '<nav class="lang-toggle" aria-label="Idioma / Language">\n'
        f'      {_link("pt", "PT", "pt-BR")}\n'
        f'      {_link("en", "EN", "en")}\n'
        "    </nav>"
    )
    t, n = re.subn(r'<div class="lang-toggle".*?</div>', seletor, t, count=1, flags=re.S)
    assert n == 1, "seletor de idioma não encontrado"

    # Nenhum JavaScript nas páginas geradas.
    t, n = re.subn(r"\n*<script>.*?</script>\n*", "\n", t, count=1, flags=re.S)
    assert n == 1, "script não encontrado"

    assert "data-pt" not in t and "data-en" not in t and "i18n" not in t, "sobrou marcação de i18n"
    return t


def main():
    verificar = "--check" in sys.argv[1:]
    desatualizados = []
    for caminho, lang in SAIDAS.items():
        alvo = RAIZ / caminho
        novo = gerar(lang)
        if verificar:
            if not alvo.exists() or alvo.read_text(encoding="utf-8") != novo:
                desatualizados.append(caminho)
        else:
            alvo.parent.mkdir(parents=True, exist_ok=True)
            alvo.write_text(novo, encoding="utf-8", newline="\n")
            print(f"gerado {caminho} ({lang})")
    if verificar:
        if desatualizados:
            print("Desatualizados (rode: python3 scripts/gerar.py): " + ", ".join(desatualizados))
            sys.exit(1)
        print("ok: páginas geradas estão em dia com src/cv.html")


if __name__ == "__main__":
    main()
