// Cloudflare Pages Function — só a raiz ("/").
//
// O idioma padrão é decidido pelo domínio, no servidor (sem JavaScript no
// navegador e sem redirecionamento, então a URL não muda e buscadores veem o
// conteúdo certo):
//   bmoraes.com  (e www.)  -> inglês   (en/index.html)
//   qualquer outro host    -> português (index.html, inclusive bmoraes.com.br)
//
// /pt/ e /en/ continuam acessíveis em qualquer domínio (é pra onde o seletor
// PT/EN aponta). Se esta Function não rodar, "/" cai no index.html estático,
// que é o português — o fallback seguro.
export async function onRequest({ request, env }) {
  const url = new URL(request.url);
  const host = url.hostname.replace(/^www\./, "");

  if (host === "bmoraes.com") {
    url.pathname = "/en/";
    const resposta = await env.ASSETS.fetch(new Request(url.toString(), request));
    const saida = new Response(resposta.body, resposta);
    saida.headers.set("Content-Language", "en");
    return saida;
  }

  const resposta = await env.ASSETS.fetch(request);
  const saida = new Response(resposta.body, resposta);
  saida.headers.set("Content-Language", "pt-BR");
  return saida;
}
