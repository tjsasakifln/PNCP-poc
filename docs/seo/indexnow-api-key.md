# IndexNow — Guia Operacional SmartLic

**Objetivo:** Configurar IndexNow para notificar motores de busca (Bing, Yandex, Seznam, Naver e parceiros) automaticamente sempre que o `sitemap.xml` do SmartLic for atualizado. Isso acelera a indexação de URLs novas ou alteradas de dias/semanas para minutos.

**Status:** Suporte oficial do Bing e Yandex desde 2021. O Google não participa do protocolo IndexNow, mas indexa via sitemap tradicional e Google Search Console (que é outra camada, não substitui IndexNow).

**Documentação oficial:** https://www.indexnow.org/

---

## 1. O que é IndexNow (resumo)

IndexNow é um protocolo aberto que permite que sites notifiquem motores de busca quando URLs são criadas, atualizadas ou removidas. Em vez de esperar o crawler descobrir mudanças (ciclo de dias a semanas), o site envia um POST com a lista de URLs e o motor de busca reage em minutos.

**Como funciona:**
1. O site gera uma chave (key) de 8-128 caracteres hexadecimais.
2. A chave é publicada em um arquivo `{key}.txt` acessível publicamente (ex: `https://smartlic.tech/abc123.txt`).
3. Ao atualizar conteúdo, o site envia POST para `https://api.indexnow.org/indexnow` contendo a lista de URLs + a key + a keyLocation (URL do arquivo `.txt`).
4. O motor de busca valida que a key publicada bate com a enviada e processa as URLs.

**Por que importa para SmartLic:**
- Páginas de conteúdo (`/features`, `/pricing`, `/ajuda`, landing pages como `/relatorio-2026-t1`) precisam ser indexadas rapidamente.
- Páginas novas do playbook SEO devem ser descobertas em minutos, não dias.
- Zero custo, zero manutenção após configuração.

---

## 2. Como gerar a key (32 caracteres hex)

A key deve ter entre 8 e 128 caracteres. Recomendamos 32 hex chars (equivalente a um UUID sem hífens) — balanço entre segurança e brevidade.

### Opção A — Node.js one-liner

```bash
node -e "console.log(require('crypto').randomBytes(16).toString('hex'))"
```

Saída exemplo:
```
a3f9c7e1b4d6028f5a8c2e9b6d4f3a1c
```

### Opção B — Python one-liner

```bash
python -c "import secrets; print(secrets.token_hex(16))"
```

Saída exemplo:
```
d8e2f1a9c7b4630e5a8f2c9d6b4e3f1a
```

### Opção C — OpenSSL (fallback universal)

```bash
openssl rand -hex 16
```

### Opção D — PowerShell (Windows nativo)

```powershell
-join ((48..57) + (97..102) | Get-Random -Count 32 | ForEach-Object {[char]$_})
```

**Importante:** execute apenas UMA VEZ e guarde a key em local seguro. Se regenerar, todos os motores de busca que já validaram a key precisarão revalidar — não é quebra crítica, mas atrasa indexação por algumas horas.

---

## 3. Hospedagem do arquivo de verificação

A key deve ser hospedada em um arquivo `.txt` estático servido pelo domínio principal (ou subdomínio).

**Caminho no SmartLic (Next.js 16):**
```
frontend/public/{key}.txt
```

**Conteúdo do arquivo:** A própria key, sem quebra de linha extra, sem aspas, sem BOM.

Exemplo — se a key gerada for `a3f9c7e1b4d6028f5a8c2e9b6d4f3a1c`:
```
Arquivo: frontend/public/a3f9c7e1b4d6028f5a8c2e9b6d4f3a1c.txt
Conteúdo: a3f9c7e1b4d6028f5a8c2e9b6d4f3a1c
```

Após o próximo deploy, o arquivo deve estar acessível em:
```
https://smartlic.tech/a3f9c7e1b4d6028f5a8c2e9b6d4f3a1c.txt
```

**Validação rápida via curl:**
```bash
curl -s https://smartlic.tech/{key}.txt
# Deve retornar exatamente a key, nada mais.
```

**Validação do content-type:** Next.js serve arquivos em `public/` como `text/plain` por padrão. Se estiver atrás de Cloudflare, confirmar que não está sendo minificado ou transformado.

---

## 4. Configuração no GitHub Actions (secret)

A GH Action que dispara o POST para IndexNow precisa ler a key sem expô-la no log ou no código-fonte.

**Passo a passo:**

1. Acessar o repositório no GitHub: `https://github.com/{owner}/pncp-poc`
2. Ir em **Settings → Secrets and variables → Actions**
3. Clicar em **New repository secret**
4. Preencher:
   - **Name:** `INDEXNOW_KEY`
   - **Secret:** valor da key gerada (ex: `a3f9c7e1b4d6028f5a8c2e9b6d4f3a1c`)
5. Clicar em **Add secret**

**No workflow YAML:** a Action acessa a key via `${{ secrets.INDEXNOW_KEY }}`. A key nunca aparece no log (o GitHub Actions redige automaticamente).

**Secret adicional recomendado (opcional):**
- `INDEXNOW_HOST` = `smartlic.tech` (caso queira parametrizar o host em vez de hardcode no workflow)

---

## 5. Validação end-to-end

Após o primeiro deploy com o arquivo `.txt` publicado e a GH Action configurada:

### 5.1. Validar keyLocation

```bash
curl -v https://smartlic.tech/{key}.txt
```

**Esperado:**
- HTTP 200
- `Content-Type: text/plain`
- Body = key exata
- Se Cloudflare está na frente, cabeçalho `CF-Cache-Status` deve estar presente e eventualmente `HIT` após primeiro acesso

### 5.2. POST manual de teste ao endpoint IndexNow

Usar curl para simular o envio que a GH Action fará:

```bash
curl -i -X POST "https://api.indexnow.org/indexnow" \
  -H "Content-Type: application/json; charset=utf-8" \
  -d '{
    "host": "smartlic.tech",
    "key": "{key}",
    "keyLocation": "https://smartlic.tech/{key}.txt",
    "urlList": [
      "https://smartlic.tech/",
      "https://smartlic.tech/features",
      "https://smartlic.tech/pricing"
    ]
  }'
```

**Códigos de resposta:**

| Código | Significado | Ação |
|--------|-------------|------|
| `200 OK` | URLs aceitas e processadas | Sucesso |
| `202 Accepted` | Recebido, pendente de validação da key | Normal na primeira submissão |
| `400 Bad Request` | JSON malformado, host inválido, key fora do range | Verificar payload |
| `403 Forbidden` | Key não bate com conteúdo do arquivo `.txt` | Revalidar arquivo + key no secret |
| `422 Unprocessable Entity` | URLs não pertencem ao host declarado | Verificar domínio |
| `429 Too Many Requests` | Rate limit atingido | Esperar, não reenviar em loop |

### 5.3. Validar no Bing Webmaster Tools

1. Acessar https://www.bing.com/webmasters
2. Fazer login com conta Microsoft (criar se não tiver)
3. Adicionar o site `smartlic.tech` e verificar propriedade
4. No menu lateral, ir em **IndexNow**
5. O painel mostrará:
   - URLs submetidas nas últimas 24h / 7 dias / 30 dias
   - Taxa de aceitação
   - Erros (se houver)

**Tempo esperado para aparecer dados:** 1-6 horas após o primeiro POST bem-sucedido.

---

## 6. Integração com sitemap.xml

A estratégia recomendada é:

1. **sitemap.xml** (em `app/sitemap.ts` no Next.js 16) continua sendo a fonte canônica de URLs indexáveis — serve Google, Bing e qualquer crawler.
2. **IndexNow** é camada adicional: sempre que o sitemap é gerado/alterado, a GH Action extrai a lista de URLs e dispara POST para IndexNow.
3. Isso significa que ao fazer deploy de uma nova página:
   - sitemap.xml é atualizado automaticamente (Next.js regenera no build)
   - GH Action detecta mudança e chama IndexNow
   - Google descobre via crawl normal do sitemap (dias)
   - Bing/Yandex descobrem via IndexNow (minutos)

**Arquivo relacionado:** `frontend/app/sitemap.ts` — deve exportar todas as URLs indexáveis (páginas públicas, não proteger rotas autenticadas).

---

## 7. Troubleshooting comum

### Problema: POST retorna 403 Forbidden

**Causas possíveis:**
1. Arquivo `{key}.txt` não está acessível publicamente (404 ou redirect)
2. Conteúdo do arquivo não bate exatamente com a key enviada (caracteres extras, whitespace, BOM)
3. Arquivo está sendo servido com Content-Type diferente de `text/plain`
4. Cloudflare bloqueando requests do crawler IndexNow por WAF

**Fix:**
```bash
# 1. Verificar content exato (sem whitespace)
curl -s https://smartlic.tech/{key}.txt | xxd

# 2. Verificar Content-Type
curl -sI https://smartlic.tech/{key}.txt | grep -i content-type

# 3. Se Cloudflare: criar rule para permitir bots do IndexNow (User-Agents incluem IndexNowBot, bingbot)
```

### Problema: POST retorna 422 Unprocessable

**Causa:** URLs no `urlList` contêm hosts diferentes do `host` declarado. Ex: `host: smartlic.tech` mas URL tem `www.smartlic.tech`.

**Fix:** normalizar host. Decidir entre `smartlic.tech` e `www.smartlic.tech` (recomendação: sem www para SmartLic, alinhado com canonical tags) e usar consistentemente em todo lugar.

### Problema: URLs aceitas mas não aparecem no Bing

**Causas possíveis:**
1. URLs têm `noindex` em meta tags
2. robots.txt está bloqueando
3. Conteúdo é duplicado (Bing detecta e prioriza canônica)
4. Site muito novo — Bing valida reputação antes de indexar

**Fix:**
```bash
# Verificar robots.txt
curl https://smartlic.tech/robots.txt

# Verificar meta robots na página
curl -s https://smartlic.tech/features | grep -i 'meta name="robots"'
```

Pode levar 24-72h para aparecer nos resultados mesmo após aceitação.

### Problema: GH Action falha ao ler INDEXNOW_KEY

**Causa:** Secret nomeado incorretamente ou não configurado no repositório correto (fork vs upstream).

**Fix:** Verificar em Settings → Secrets → Actions se `INDEXNOW_KEY` aparece na lista. Reexecutar workflow após criar.

### Problema: Rate limit 429

**Causa:** Submissões muito frequentes ou em lote gigante (>10.000 URLs por request).

**Fix:** Limitar a 1 POST por minuto, máximo 10.000 URLs por request. Se precisar enviar mais, quebrar em batches com sleep de 60s entre eles.

---

## 8. Checklist de setup completo

- [ ] Key de 32 hex chars gerada e armazenada em local seguro (1Password, Bitwarden, etc.)
- [ ] Arquivo `frontend/public/{key}.txt` criado com conteúdo = key
- [ ] Commit feito no repositório (arquivo deve estar trackado no git)
- [ ] Deploy em produção concluído
- [ ] `curl https://smartlic.tech/{key}.txt` retorna a key exata (HTTP 200)
- [ ] Secret `INDEXNOW_KEY` configurado em GitHub → Settings → Secrets → Actions
- [ ] GH Action de notificação IndexNow criada e rodando (responsabilidade de outra frente do playbook)
- [ ] POST manual de teste retornou 200 ou 202
- [ ] Bing Webmaster Tools conectado, propriedade verificada, painel IndexNow acessível
- [ ] Primeira submissão real após deploy refletida no painel Bing em até 6h
- [ ] Documentação interna atualizada com localização da key e procedimento de rotação

---

## 9. Rotação de key (futuro)

Se houver suspeita de comprometimento (ex: key acidentalmente commitada em código público), rotacionar:

1. Gerar nova key (seção 2)
2. Criar novo arquivo `frontend/public/{new_key}.txt`
3. **Manter o arquivo antigo por 7 dias** (para não invalidar submissões recentes enquanto os crawlers revalidam)
4. Atualizar secret `INDEXNOW_KEY` no GitHub
5. Re-executar workflow manualmente para validar
6. Após 7 dias, remover arquivo antigo
7. Documentar data da rotação

---

## 10. Referências

- **Site oficial:** https://www.indexnow.org/
- **Documentação Bing:** https://www.bing.com/indexnow/
- **Documentação Yandex:** https://yandex.com/support/webmaster/indexnow/
- **API endpoint principal:** `https://api.indexnow.org/indexnow`
- **Endpoints alternativos (específicos por motor):**
  - Bing: `https://www.bing.com/indexnow`
  - Yandex: `https://yandex.com/indexnow`
- **Limites operacionais:** 10.000 URLs por request, no máximo 1 request por segundo por host
- **Arquivos SmartLic relacionados:** `frontend/app/sitemap.ts`, `frontend/public/{key}.txt`, `.github/workflows/indexnow.yml` (criado em outra frente do playbook)
