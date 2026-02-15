# GTM-009: Reescrita da Features Page — Transformação, Não Tarefa

| Metadata | Value |
|----------|-------|
| **ID** | GTM-009 |
| **Priority** | P1 |
| **Sprint** | 2 |
| **Estimate** | 6h |
| **Type** | GTM (Go-to-Market) |
| **Dependencies** | GTM-008 (IA reposicionada) |
| **Blocks** | — |
| **Status** | Pending |
| **Created** | 2026-02-15 |
| **Squad** | Content + Dev (Frontend) |

---

## Problem Statement

### Narrativa de Tarefa vs. Narrativa de Transformação

**Problema central:** A features page atual compara **tarefas** ("busca manual" vs "busca automatizada") em vez de **cenários de resultado** ("perder oportunidades" vs "ganhar licitações").

#### Estrutura Atual (Problemática)

| Feature Atual | Foco | Por Que É Insuficiente |
|---------------|------|------------------------|
| "Busca por Setor" | Tarefa: "Selecione seu setor e encontramos variações" | Não comunica valor. É recurso técnico, não benefício. |
| "Filtragem Inteligente" | Métrica: "95% de precisão, zero ruído" | Métrica abstrata. Usuário não sente impacto de "95% vs 80%". |
| "PNCP + 27 Portais" | Funcionalidade: "Consolidação de fontes" | Não comunica **por que** consolidação importa. |
| "Resultado em 3 Minutos" | Eficiência: "160x mais rápido" | Vende velocidade (commodity), não resultado. |
| "Resumos Executivos IA" | Tarefa: "Decida em 30 segundos" | Foca em tempo economizado, não em decisão melhor. |

### O Que Falta

A features page não responde:

1. **"O que muda no MEU resultado?"** (não "o que a ferramenta faz")
2. **"Qual o custo de NÃO usar SmartLic?"** (criar urgência real)
3. **"Como isso me dá vantagem sobre meus concorrentes?"** (contexto competitivo)

### Diretriz Estratégica

> **Cada feature deve narrar uma transformação:** cenário ruim (sem SmartLic) → cenário bom (com SmartLic).

Comparação deve ser: **"perder licitações por falta de visibilidade"** vs **"entrar preparado nas oportunidades certas"**.

---

## Solution/Scope

### Features Novas (Substituem as Atuais)

#### 1. Priorização Inteligente
**Substitui:** "Busca por Setor"

**Antes (copy atual):**
> "Selecione seu setor (uniformes, facilities, tecnologia...) e encontramos todas as variações de palavras-chave. Não perca nenhuma oportunidade por falta de terminologia."

**Depois (nova copy):**
> **"Foco no Que Realmente Importa"**
>
> **Sem SmartLic:** Você gasta tempo lendo editais incompatíveis com seu perfil, perde oportunidades boas por não saber que existem.
>
> **Com SmartLic:** O sistema avalia cada oportunidade com base no seu perfil (porte, região, ticket médio) e indica quais merecem sua atenção. Você para de desperdiçar tempo com licitações ruins e foca nas que pode ganhar.

**Arquivo:** `frontend/app/features/page.tsx` — seção 1

---

#### 2. Análise de Adequação
**Substitui:** "Filtragem Inteligente"

**Antes (copy atual):**
> "95% de precisão, zero ruído. Filtramos milhares de licitações irrelevantes e entregamos apenas as que importam para você."

**Depois (nova copy):**
> **"Você Decide Sem Ler 100 Páginas de Edital"**
>
> **Sem SmartLic:** Você baixa edital de 120 páginas, lê por 40 minutos, descobre que requisitos são incompatíveis. Tempo perdido.
>
> **Com SmartLic:** Não precisa ler editais para decidir se vale a pena. O SmartLic avalia requisitos, prazos e valores contra seu perfil e diz: "Vale a pena" ou "Pule esta". Você decide em segundos com base em critérios objetivos.

**Arquivo:** `frontend/app/features/page.tsx` — seção 2

---

#### 3. Cobertura Nacional Consolidada
**Substitui:** "PNCP + 27 Portais" (mantém conceito, muda narrativa)

**Antes (copy atual):**
> "Consultamos PNCP federal + 27 portais estaduais. Tudo consolidado em um só lugar."

**Depois (nova copy):**
> **"Você Nunca Perde uma Oportunidade Por Não Saber Que Ela Existe"**
>
> **Sem SmartLic:** Você consulta 3-4 fontes manualmente. Oportunidades em portais estaduais passam despercebidas. Seu concorrente descobre antes.
>
> **Com SmartLic:** Consulta em tempo real dezenas de fontes oficiais, federais e estaduais. Cobertura nacional completa. Se uma licitação compatível com seu perfil é publicada em qualquer lugar do Brasil, você sabe.

**Arquivo:** `frontend/app/features/page.tsx` — seção 3

**Nota:** Alinha com GTM-007 (sem mencionar "PNCP" explicitamente).

---

#### 4. Inteligência de Decisão
**Substitui:** "Resultado em 3 Minutos"

**Antes (copy atual):**
> "160x mais rápido que busca manual. Resultado completo em 3 minutos. Economize 8 horas por semana."

**Depois (nova copy):**
> **"Decisões Melhores, Não Apenas Mais Rápidas"**
>
> **Sem SmartLic:** Você encontra licitações, mas não sabe quais priorizar. Entra em todas e se dispersa. Taxa de sucesso baixa.
>
> **Com SmartLic:** Avalie uma oportunidade em segundos com base em critérios objetivos (adequação, competitividade, requisitos). Não é sobre ser rápido — é sobre decidir melhor. Você investe tempo onde tem chance real de ganhar.

**Arquivo:** `frontend/app/features/page.tsx` — seção 4

**Nota:** Alinha com GTM-008 (IA como orientação de decisão).

---

#### 5. Vantagem Competitiva
**Substitui:** "Resumos Executivos IA"

**Antes (copy atual):**
> "IA gera resumos executivos de 3 linhas. Decida em 30 segundos, não em 20 minutos."

**Depois (nova copy):**
> **"Seu Concorrente Ainda Está Procurando. Você Já Está Se Posicionando."**
>
> **Sem SmartLic:** Você descobre oportunidades dias depois da publicação. Concorrentes já estão preparando propostas. Você entra atrasado.
>
> **Com SmartLic:** Notificações em tempo real de novas oportunidades compatíveis com seu perfil. Você descobre antes, se posiciona antes, compete melhor. Quem encontra primeiro tem vantagem.

**Arquivo:** `frontend/app/features/page.tsx` — seção 5

**Nota:** Introduz elemento competitivo (urgência real, não artificial).

---

### Hero da Features Page

**Antes (copy atual):**
> "Funcionalidades do SmartLic"
>
> "Conheça os recursos que tornam o SmartLic a plataforma mais completa de licitações do Brasil."

**Depois (nova copy):**
> "O Que Muda no Seu Resultado"
>
> "SmartLic não é sobre fazer tarefas mais rápido. É sobre transformar como você encontra, avalia e decide em quais licitações investir tempo. Compare os cenários:"

**Arquivo:** `frontend/app/features/page.tsx` — hero section

---

### CTA Final da Features Page

**Antes (copy atual):**
> "Economize Tempo, Encontre Mais Oportunidades"
>
> [CTA: "Começar Agora"]

**Depois (nova copy):**
> "Começar a Ganhar Mais Licitações"
>
> Experimente o SmartLic completo por 7 dias. Sem versão limitada. Se uma única licitação ganha pagar o sistema por um ano inteiro, por que esperar?
>
> [CTA: "Experimentar SmartLic Pro"]

**Arquivo:** `frontend/app/features/page.tsx` — CTA final

---

## Acceptance Criteria

### Narrativa de Transformação

- [ ] **AC1:** Cada feature (1-5) narra transformação com estrutura "Sem SmartLic" → "Com SmartLic"
  - Estrutura clara: **Título (benefício)** → **Cenário ruim** → **Cenário bom**
  - Mínimo 2 parágrafos por feature (cenário ruim + cenário bom)

- [ ] **AC2:** Features focam em resultado (ganhar vs perder licitações), não em tarefa (buscar vs não buscar)
  - ❌ "Encontre licitações 160x mais rápido"
  - ✅ "Você investe tempo onde tem chance real de ganhar"

### Eliminação de Métricas de Eficiência

- [ ] **AC3:** ZERO métricas de eficiência (tempo, velocidade, percentuais) em headlines
  - Eliminar: "160x", "95%", "3 minutos", "8 horas", "30 segundos"
  - Exceção: Métricas podem aparecer em suporte (não como headline)

- [ ] **AC4:** Nenhuma feature usa "mais rápido", "economiza tempo", "em X minutos" como benefício principal

### Custo de Não Usar

- [ ] **AC5:** Custo de não usar presente em **pelo menos 2 features** (idealmente todas)
  - Exemplos: "Oportunidades passam despercebidas", "Você entra atrasado", "Tempo perdido lendo editais incompatíveis"

### Contexto Competitivo

- [ ] **AC6:** Competição/concorrente mencionado em **pelo menos 1 feature** (idealmente 2)
  - Exemplos: "Seu concorrente descobre antes", "Concorrentes já estão preparando propostas"
  - Cria urgência real (não artificial tipo "oferta limitada")

### Hero e CTA

- [ ] **AC7:** Hero da features page usa headline focada em resultado
  - **Atual:** "Funcionalidades do SmartLic"
  - **Novo:** "O Que Muda no Seu Resultado"

- [ ] **AC8:** CTA final usa verbo de resultado (não de eficiência)
  - ❌ "Economizar Tempo"
  - ✅ "Começar a Ganhar Mais Licitações"

### Alinhamento com Outras Stories GTM

- [ ] **AC9:** Features não mencionam "PNCP" explicitamente (alinha com GTM-007)
  - Usa "fontes oficiais", "cobertura nacional", "dezenas de fontes"

- [ ] **AC10:** IA descrita como "avaliação" e "orientação de decisão" (alinha com GTM-008)
  - Não usa "resumo", "resumo executivo"

- [ ] **AC11:** Trial descrito como "produto completo por 7 dias" (alinha com GTM-003)
  - CTA final menciona "Experimente SmartLic Pro" (plano único, alinha com GTM-002)

---

## Definition of Done

- [ ] Todos os Acceptance Criteria marcados como concluídos
- [ ] 5 features reescritas com estrutura de transformação
- [ ] Hero e CTA final atualizados
- [ ] ZERO métricas de eficiência em headlines (grep validation)
- [ ] Custo de não usar presente em ≥2 features
- [ ] Contexto competitivo presente em ≥1 feature
- [ ] Build passa (TypeScript clean, lint clean)
- [ ] Mobile responsive testado (375px, 768px, 1024px)
- [ ] PR aberto, revisado e merged
- [ ] Deploy em staging verificado (audit manual de copy e estrutura)

---

## Technical Notes

### Estrutura de Componente (Sugestão)

```tsx
// frontend/app/features/page.tsx

interface FeatureTransformProps {
  title: string;
  without: string; // Cenário sem SmartLic
  with: string;    // Cenário com SmartLic
  gemAccent?: 'sapphire' | 'emerald' | 'amethyst' | 'ruby';
}

function FeatureTransform({ title, without, with, gemAccent }: FeatureTransformProps) {
  return (
    <GlassCard variant="feature" gemAccent={gemAccent}>
      <h3 className="text-2xl font-bold mb-6">{title}</h3>

      <div className="grid md:grid-cols-2 gap-8">
        <div className="space-y-2">
          <div className="flex items-center gap-2 text-red-500">
            <XCircle className="w-5 h-5" />
            <span className="font-semibold">Sem SmartLic</span>
          </div>
          <p className="text-gray-600 dark:text-gray-300">{without}</p>
        </div>

        <div className="space-y-2">
          <div className="flex items-center gap-2 text-green-500">
            <CheckCircle className="w-5 h-5" />
            <span className="font-semibold">Com SmartLic</span>
          </div>
          <p className="text-gray-600 dark:text-gray-300">{with}</p>
        </div>
      </div>
    </GlassCard>
  );
}

// Uso:
<FeatureTransform
  title="Foco no Que Realmente Importa"
  without="Você gasta tempo lendo editais incompatíveis com seu perfil..."
  with="O sistema avalia cada oportunidade com base no seu perfil..."
  gemAccent="sapphire"
/>
```

### Alinhamento com Design System (GTM-006)

Se GTM-006 já foi implementado:
- Usar `<GlassCard variant="feature">` para cada feature
- Aplicar gems accent conforme contexto:
  - **Esmeralda** (verde): Features relacionadas a sucesso/ganhar
  - **Safira** (azul): Features relacionadas a decisão/inteligência
  - **Ametista** (roxo): Features relacionadas a vantagem premium
  - **Rubi** (vermelho): Features relacionadas a urgência/competição

### Copy Writing Guidelines

**Estrutura de cada feature:**

1. **Título (10-15 palavras):** Benefício tangível, não funcionalidade técnica
   - ❌ "Filtragem Inteligente"
   - ✅ "Você Decide Sem Ler 100 Páginas de Edital"

2. **Cenário sem SmartLic (30-50 palavras):** Dor específica, tangível, relatable
   - Usar 2ª pessoa ("Você...")
   - Detalhar consequência ruim
   - Exemplo: "Você baixa edital de 120 páginas, lê por 40 minutos, descobre que requisitos são incompatíveis. Tempo perdido."

3. **Cenário com SmartLic (40-60 palavras):** Como SmartLic resolve a dor, resultado esperado
   - Usar 2ª pessoa ("Você...")
   - Foco em resultado, não em como funciona tecnicamente
   - Exemplo: "O SmartLic avalia requisitos, prazos e valores contra seu perfil e diz: 'Vale a pena' ou 'Pule esta'. Você decide em segundos com base em critérios objetivos."

---

## Validation Checklist (Pós-Implementação)

```bash
#!/bin/bash
# validate-features-transformation.sh

echo "🔍 Validating features page transformation..."

# Check for banned efficiency metrics
echo "\n🚫 Checking for efficiency metrics in headlines:"
EFFICIENCY_MATCHES=$(grep -ri "160x\|95%\|3 minutos\|8 horas\|mais rápido" \
  frontend/app/features/page.tsx \
  2>/dev/null | wc -l)

if [ "$EFFICIENCY_MATCHES" -eq 0 ]; then
  echo "✅ PASS: Zero efficiency metrics in headlines"
else
  echo "❌ FAIL: Found $EFFICIENCY_MATCHES efficiency metrics"
  grep -i "160x\|95%\|3 minutos" frontend/app/features/page.tsx
fi

# Check for transformation structure
echo "\n✅ Checking for transformation keywords:"
grep -i "Sem SmartLic\|Com SmartLic" frontend/app/features/page.tsx | head -5

# Check for competitive context
echo "\n🏆 Checking for competitive mentions:"
grep -i "concorrente\|competição\|compete" frontend/app/features/page.tsx | head -3

echo "\n✅ Validation complete"
```

---

## File List

### Frontend (Must Update)
- `frontend/app/features/page.tsx` (reescrita completa: hero, 5 features, CTA final)

### Frontend (Reference for Copy Alignment)
- `frontend/lib/copy/valueProps.ts` (garantir consistência de linguagem)
- `frontend/app/components/landing/HowItWorks.tsx` (consistência de narrativa)

---

## Related Stories

- **GTM-001:** Landing page rewrite (narrativa de transformação já aplicada)
- **GTM-007:** PNCP sanitization (features não mencionam "PNCP")
- **GTM-008:** IA reposicionamento (features descrevem IA como "avaliação", não "resumo")
- **GTM-002:** Plano único (CTA final menciona "SmartLic Pro")
- **GTM-003:** Trial completo (CTA final menciona "7 dias do produto completo")

---

*Story created from consolidated GTM backlog 2026-02-15*
