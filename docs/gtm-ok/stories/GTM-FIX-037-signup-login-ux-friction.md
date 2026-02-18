# GTM-FIX-037: Fricção no fluxo de Signup/Login

**Priority:** P2 (impacta conversão mas não bloqueia uso)
**Effort:** S (2-3h)
**Origin:** Teste de produção manual 2026-02-18
**Status:** CONCLUÍDO
**Assignee:** @dev + @ux-design-expert
**Tracks:** Frontend (3 ACs)

---

## Problem Statement

O fluxo de signup e login tem pontos de fricção que podem impactar conversão de novos usuários.

### Problemas Identificados

#### ~~1. Sem botão "Entrar" / "Login" na navbar da landing page~~
**INVALIDADO**: `LandingNavbar.tsx:76-104` já tem lógica condicional — mostra "Login" + "Criar conta" para não-autenticados, e "Ir para Busca" para autenticados. O teste foi feito com sessão ativa, por isso só aparecia "Ir para Busca".

#### 2. Botão "Criar conta" disabled sem explicação
Ao abrir a página de signup, o botão está cinza/disabled. Não há tooltip ou texto explicando "Preencha todos os campos". O usuário pode pensar que está quebrado.

#### 3. Email inválido sem feedback
Se o usuário digita "invalido" (sem @) no campo email, o botão fica disabled mas **não há mensagem de erro de email**. As validações de senha aparecem inline (checklist visual), mas a de email não.

#### 4. Campo "Confirmar senha" é fricção extra
Para um trial grátis sem cartão, 4 campos (nome, email, senha, confirmar senha) já são mais que o mínimo. "Confirmar senha" adiciona fricção para um fluxo onde o erro é facilmente recuperável (reset password).

---

## Acceptance Criteria

### Frontend

- [x] **AC1**: Mostrar mensagem de validação inline para email inválido (ex: "Digite um email válido") quando o campo perde foco e não contém "@" + domínio. Similar à checklist visual já existente para senha.
- [x] **AC2**: Quando botão "Criar conta" está disabled, mostrar texto discreto abaixo: "Preencha todos os campos corretamente para continuar."
- [x] **AC3**: Removido campo "Confirmar senha" — o toggle "Mostrar senha" já cobre a necessidade. Formulário reduzido de 4 para 3 campos.

---

## Arquivos Exatos

| Arquivo | Linhas | O que mudar |
|---------|--------|-------------|
| `frontend/app/signup/page.tsx` | ~108-113, ~332, ~442 | Validação email inline + hint botão disabled |
| `frontend/app/components/landing/LandingNavbar.tsx` | 76-104 | ~~AC1 removido~~ — já tem Login para não-auth |

## Technical Notes

- Navbar da landing: `app/components/landing/LandingNavbar.tsx:76-104` — já tem lógica condicional auth/non-auth
- Signup form: `app/signup/page.tsx` — validações inline estão em linhas 108-113 (senha), mas email não tem validação visual equivalente
- O toggle "Mostrar senha" já existe (botão ao lado do campo), o que mitiga a necessidade de "Confirmar senha"
