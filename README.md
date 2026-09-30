# cv

Site pessoal de currículo, em português e inglês:

- [bmoraes.com.br](https://bmoraes.com.br) abre em **português**
- [bmoraes.com](https://bmoraes.com) abre em **inglês**

Os dois domínios servem o mesmo projeto no Cloudflare Pages (build command: nenhum; output directory: `/`). `/pt/` e `/en/` funcionam em qualquer um deles e é pra onde o seletor PT/EN aponta.

## Como funciona

- `src/cv.html` é a **fonte**: um único arquivo com os dois idiomas (`data-pt` / `data-en` em cada trecho traduzível).
- `scripts/gerar.py` gera páginas estáticas de verdade, sem JavaScript, cada uma com `<html lang>`, título, descrição, `canonical` e `hreflang` próprios:
  `index.html` (pt), `pt/index.html` (pt) e `en/index.html` (en).
- `functions/index.js` (Cloudflare Pages Function) escolhe o idioma da **raiz** pelo domínio: `bmoraes.com` serve `en/index.html`, o resto serve `index.html`. Se a Function falhar, a raiz cai no português estático.

## Editar o currículo

1. Altere **só** `src/cv.html`.
2. `python3 scripts/gerar.py` (e `--check` pra conferir se as páginas estão em dia).
3. Commit dos arquivos gerados junto com a fonte (o Pages publica sem etapa de build).

## Testar localmente

`python3 -m http.server` na raiz mostra `/`, `/pt/` e `/en/` (a raiz sempre em português; a troca por domínio só existe no Cloudflare).
