# STORY-166: Adicionar Campos de Perfil e Consentimento no Cadastro

**Epic:** User Management
**Priority:** High
**Points:** 8
**Status:** Implemented

## User Story

**Como** visitante do SmartLic,
**Quero** preencher meu perfil completo durante o cadastro e aceitar os termos de consentimento,
**Para que** eu possa receber ofertas e promoções da equipe via Email e WhatsApp.

## Contexto

O formulário de cadastro atual foi expandido com campos adicionais para captura de informações
de perfil completas e consentimento LGPD para comunicações promocionais.

## Campos Adicionados

1. **Empresa** (obrigatório) - Nome da empresa do usuário
2. **Setor de Atuação** (obrigatório) - Dropdown com 12 setores + opção "Outro"
3. **Telefone WhatsApp** (obrigatório) - Com máscara de formato brasileiro
4. **Termos de Consentimento** (obrigatório) - Scroll até o fim para aceitar
5. **Checkbox de Aceite** - Habilitado apenas após scroll completo

## Acceptance Criteria

### AC1: Campo de Empresa
- [x] Campo de empresa adicionado após o campo de nome
- [x] Campo obrigatório
- [x] Placeholder: "Nome da sua empresa"

### AC2: Campo de Setor de Atuação
- [x] Dropdown com 12 setores pré-definidos + "Outro"
- [x] Campo obrigatório
- [x] Se "Outro" selecionado, exibir campo de texto para digitar o setor

### AC3: Campo de Telefone WhatsApp
- [x] Campo de telefone com ícone WhatsApp verde
- [x] Placeholder: "(11) 99999-9999"
- [x] Máscara de input para formato brasileiro: (XX) XXXXX-XXXX ou (XX) XXXX-XXXX
- [x] Campo obrigatório
- [x] Validação: aceitar apenas números, mínimo 10 dígitos, máximo 11

### AC4: Termos de Consentimento com Scroll
- [x] Caixa de texto com altura fixa (~150px) e scroll vertical
- [x] Texto legal sobre consentimento de mensagens promocionais via Email e WhatsApp
- [x] Indicador visual "Role para baixo" com seta animada
- [x] Detectar quando usuário rolou até o final do texto
- [x] Indicador desaparece após scroll completo

### AC5: Checkbox de Aceite
- [x] Checkbox com label "Li e aceito receber promoções e ofertas via Email e WhatsApp"
- [x] Checkbox desabilitado inicialmente (opacity 50%)
- [x] Checkbox habilitado apenas após rolar até o fim dos termos
- [x] Checkbox obrigatório para finalizar cadastro

### AC6: Validação do Formulário
- [x] Botão "Criar conta" desabilitado até:
  - Todos os campos preenchidos
  - Setor válido (ou campo "outro" preenchido)
  - Telefone válido (10-11 dígitos)
  - Checkbox de consentimento marcado
- [x] Mensagens de erro claras para cada validação

### AC7: Persistência no Banco
- [x] Migration SQL para adicionar colunas na tabela `profiles`:
  - `sector TEXT`
  - `phone_whatsapp TEXT`
  - `whatsapp_consent BOOLEAN DEFAULT FALSE`
  - `whatsapp_consent_at TIMESTAMPTZ`
- [x] Constraint de validação para formato de telefone
- [x] Índice para busca de usuários com consentimento
- [x] Atualizar trigger `handle_new_user()` para incluir novos campos
- [x] Atualizar `signUpWithEmail` para passar os dados via `user_metadata`

### AC8: Testes
- [x] Testes unitários para validação de telefone
- [x] Testes unitários para comportamento do scroll
- [x] Testes unitários para campo de setor e "outro"
- [x] Teste E2E do fluxo completo de cadastro

## Setores Disponíveis

1. Vestuário e Uniformes
2. Alimentos e Merenda
3. Informática e Tecnologia
4. Mobiliário
5. Papelaria e Material de Escritório
6. Engenharia e Construção
7. Software e Sistemas
8. Facilities (Limpeza e Zeladoria)
9. Saúde
10. Vigilância e Segurança
11. Transporte e Veículos
12. Manutenção Predial
13. Outro (com campo de texto)

## Technical Details

### Arquivos Modificados

| Arquivo | Mudança |
|---------|---------|
| `frontend/app/signup/page.tsx` | Novos campos, lógica de scroll, validações, setores |
| `frontend/app/components/AuthProvider.tsx` | Atualizado `signUpWithEmail` com novos params |
| `supabase/migrations/007_add_whatsapp_consent.sql` | Nova migration com campos e trigger |
| `frontend/__tests__/pages/SignupPage.test.tsx` | Testes atualizados para novos campos |
| `frontend/e2e-tests/signup-consent.spec.ts` | Novo teste E2E completo |

### Schema da Migration

```sql
-- Novos campos
ALTER TABLE public.profiles
  ADD COLUMN IF NOT EXISTS sector TEXT,
  ADD COLUMN IF NOT EXISTS phone_whatsapp TEXT,
  ADD COLUMN IF NOT EXISTS whatsapp_consent BOOLEAN DEFAULT FALSE,
  ADD COLUMN IF NOT EXISTS whatsapp_consent_at TIMESTAMPTZ;

-- Constraint de formato de telefone brasileiro
ALTER TABLE public.profiles
  ADD CONSTRAINT phone_whatsapp_format CHECK (
    phone_whatsapp IS NULL OR
    phone_whatsapp ~ '^[0-9]{10,11}$'
  );

-- Índice para campanhas de marketing
CREATE INDEX IF NOT EXISTS idx_profiles_whatsapp_consent
  ON public.profiles(whatsapp_consent)
  WHERE whatsapp_consent = TRUE;
```

## Texto dos Termos de Consentimento

```text
TERMOS DE CONSENTIMENTO PARA COMUNICACOES PROMOCIONAIS

Ao fornecer seus dados e marcar a caixa de aceite abaixo, voce autoriza
expressamente a equipe do SmartLic a enviar comunicacoes promocionais
por EMAIL e WHATSAPP, incluindo:

1. Mensagens promocionais sobre novos recursos e funcionalidades;
2. Ofertas especiais, descontos e pacotes promocionais;
3. Dicas e conteudos relevantes sobre licitacoes publicas;
4. Lembretes sobre oportunidades de licitacao compativeis com seu perfil.

FREQUENCIA: As mensagens serao enviadas com moderacao, respeitando horarios
comerciais (segunda a sexta, 9h as 18h).

CANCELAMENTO: Voce pode cancelar o recebimento a qualquer momento:
- Respondendo "PARAR" a qualquer mensagem de WhatsApp
- Clicando em "Descadastrar" nos emails recebidos
- Acessando as configuracoes do seu perfil
- Entrando em contato pelo email suporte@confenge.com.br

PRIVACIDADE: Seus dados (email e telefone) nao serao compartilhados com
terceiros e serao utilizados exclusivamente para as finalidades descritas acima.

Este consentimento esta em conformidade com a Lei Geral de Protecao de Dados
(LGPD - Lei n. 13.709/2018).
```

## UI/UX Highlights

- Ícone WhatsApp verde no label do campo de telefone
- Máscara automática de telefone enquanto digita
- Indicador de scroll animado (seta bounce) desaparece após atingir o fim
- Checkbox com visual disabled (opacity 50%) até scroll completo
- Campo "Qual setor?" aparece condicionalmente quando "Outro" é selecionado
- Botão de submit desabilitado com visual feedback até formulário válido

## Out of Scope

- Integração real com WhatsApp Business API (futura feature)
- Verificação de número de telefone via SMS/código
- Preferências granulares de tipos de mensagem
- Campos de endereço completo

## Definition of Done

- [x] Todos os acceptance criteria implementados
- [x] Testes unitários criados
- [x] Testes E2E criados
- [ ] Testes passando (aguardando execução)
- [ ] Migration aplicada em staging
- [ ] Code review aprovado

## File List

_Arquivos modificados durante a implementação:_

- [x] `frontend/app/signup/page.tsx`
- [x] `frontend/app/components/AuthProvider.tsx`
- [x] `supabase/migrations/007_add_whatsapp_consent.sql`
- [x] `frontend/__tests__/pages/SignupPage.test.tsx`
- [x] `frontend/e2e-tests/signup-consent.spec.ts`

---

**Created by:** @pm (Morgan)
**Implemented by:** Full Squad
**Date:** 2026-02-06
