"""
Message Generator - Create personalized outreach messages using OpenAI.

This module generates personalized sales messages based on:
- Company data
- Growth metrics and behavioral patterns
- Buy-intent scoring factors
- Sector alignment
- Strategic intelligence

STORY-184: Lead Prospecting Workflow
"""

import logging
from typing import Optional
import os

from openai import OpenAI

from schemas_lead_prospecting import (
    ContractData,
    StrategicIntelligence,
    BuyIntentScore,
    GrowthMetrics,
)

logger = logging.getLogger(__name__)


class MessageGenerator:
    """Generate personalized outreach messages using OpenAI."""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize message generator.

        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            logger.warning("OPENAI_API_KEY not set - message generation will fail")

        self.client = OpenAI(api_key=self.api_key) if self.api_key else None

    def generate_message(
        self,
        company_name: str,
        sector: str,
        recent_contract: ContractData,
        intelligence: StrategicIntelligence,
        growth_metrics: Optional[GrowthMetrics] = None,
        buy_intent_score: Optional[BuyIntentScore] = None,
        dependency_percentage: float = 0.0,
    ) -> str:
        """
        Generate personalized outreach message focused on behavioral patterns.

        The new buy-intent model shifts messaging from "we saw your contract"
        to "we understand your operational patterns and bottlenecks". The LLM
        references participation patterns, win rates, and growth trends --
        never specific contract names.

        Args:
            company_name: Company name.
            sector: Primary sector.
            recent_contract: Most recent contract win.
            intelligence: Strategic intelligence.
            growth_metrics: Computed growth metrics (new model).
            buy_intent_score: 6-factor buy-intent score (new model).
            dependency_percentage: Legacy dependency score (%) -- kept for
                backward compatibility; ignored when ``growth_metrics`` is
                provided.

        Returns:
            Personalized message (plain text).
        """
        if not self.client:
            return self._fallback_message(
                company_name, sector, recent_contract, growth_metrics
            )

        # Build prompt
        system_prompt = """Voce e um especialista em vendas B2B no setor de licitacoes publicas.
Sua tarefa e criar emails personalizados de prospeccao para empresas que participam de licitacoes.

Requisitos:
- Tom profissional mas caloroso
- Demonstrar inteligencia operacional: referenciar padroes de participacao, taxas de vitoria e tendencias de crescimento
- NAO citar nomes de contratos ou orgaos especificos
- Focar em gargalos operacionais que o SmartLic resolve (triagem, monitoramento, qualificacao)
- Exemplo de tom: "Notei que voces participaram de 18 pregoes no ultimo trimestre e venceram 3. Empresas nesse ritmo geralmente enfrentam gargalo de triagem..."
- Oferecer valor imediato (analise gratuita de oportunidades)
- Call to action: agendar 15 minutos
- Maximo 150 palavras
- NAO incluir assunto (subject line)"""

        # Build user prompt with growth metrics when available
        if growth_metrics and buy_intent_score:
            user_prompt = f"""Empresa: {company_name}
Setor: {sector}
Valor medio de contrato: R$ {growth_metrics.avg_contract_value:,.2f}

Metricas de atividade (ultimos meses):
- Participacoes: {growth_metrics.participation_count}
- Vitorias: {growth_metrics.win_count}
- Taxa de vitoria: {growth_metrics.win_rate:.0%}
- Crescimento trimestral: {growth_metrics.quarter_growth_pct:+.0f}%
- Orgaos distintos: {growth_metrics.unique_organs}
- Segmentos distintos: {growth_metrics.unique_segments}

Buy-Intent Score: {buy_intent_score.overall_score:.1f}/10
- Intensidade operacional: {buy_intent_score.operational_intensity:.0f}/10
- Crescimento recente: {buy_intent_score.recent_growth:.0f}/10
- Complexidade de portfolio: {buy_intent_score.portfolio_complexity:.0f}/10
- Sinal de gargalo: {buy_intent_score.bottleneck_signal:.0f}/10
{f"- Sinais externos: {', '.join(buy_intent_score.buy_signals)}" if buy_intent_score.buy_signals else ""}

Inteligencia: {intelligence.summary[:300]}

Crie um email personalizado demonstrando inteligencia operacional sobre a empresa."""
        else:
            # Legacy fallback when growth metrics are not available
            user_prompt = f"""Empresa: {company_name}
Setor: {sector}
Contrato Recente: {recent_contract.contract_object[:200]} (R$ {recent_contract.contract_value:,.2f})
Data: {recent_contract.contract_date}
Inteligencia: {intelligence.summary[:300]}
Dependencia de Licitacoes: {dependency_percentage:.0f}%

Crie um email personalizado de apresentacao do SmartLic."""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4.1-nano",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                max_tokens=500,
                temperature=0.7,
            )

            message = response.choices[0].message.content.strip()
            logger.debug(f"Generated message for {company_name} ({len(message)} chars)")
            return message

        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            return self._fallback_message(
                company_name, sector, recent_contract, growth_metrics
            )

    def _fallback_message(
        self,
        company_name: str,
        sector: str,
        recent_contract: ContractData,
        growth_metrics: Optional[GrowthMetrics] = None,
    ) -> str:
        """
        Generate fallback message without OpenAI (template-based).

        Uses behavioral patterns when growth_metrics is available,
        otherwise falls back to legacy contract-reference style.

        Args:
            company_name: Company name.
            sector: Primary sector.
            recent_contract: Most recent contract win.
            growth_metrics: Computed growth metrics (optional).

        Returns:
            Template-based message.
        """
        if growth_metrics and growth_metrics.participation_count > 0:
            win_rate_pct = f"{growth_metrics.win_rate:.0%}"
            growth_direction = (
                f"crescimento de {growth_metrics.quarter_growth_pct:+.0f}% no ultimo trimestre"
                if growth_metrics.quarter_growth_pct > 0
                else "volume estavel nos ultimos meses"
            )
            return f"""Ola, equipe da {company_name}!

Acompanhamos o mercado de {sector} e notamos que voces participaram de {growth_metrics.participation_count} processos recentemente, com taxa de vitoria de {win_rate_pct} e {growth_direction}.

Empresas com esse ritmo de participacao geralmente enfrentam gargalos na triagem e qualificacao de editais. O SmartLic automatiza exatamente isso: monitoramento contínuo, filtragem inteligente por setor e analise de viabilidade em segundos.

Preparei uma analise gratuita com oportunidades abertas em {sector} que se alinham ao perfil de atuacao da {company_name}.

Podemos agendar 15 minutos para eu apresentar essa analise?

Atenciosamente,
[Seu Nome]
SmartLic
[Seu Contato]"""

        # Legacy fallback (no growth metrics available)
        return f"""Ola, equipe da {company_name}!

Parabens pelo contrato recente em {sector} (R$ {recent_contract.contract_value:,.2f})!

Identificamos varias oportunidades abertas em {sector} que se alinham perfeitamente com o historico de atuacao da {company_name}.

Preparei uma planilha com essas oportunidades (anexo), incluindo licitacoes abertas em diversos estados.

O SmartLic automatiza a busca de licitacoes em todo o Brasil, filtrando por setor, regiao e valor. Empresas como a {company_name} economizam horas de prospeccao manual.

Podemos agendar 15 minutos para eu apresentar outras oportunidades que identificamos especificamente para voces?

Atenciosamente,
[Seu Nome]
SmartLic
[Seu Contato]"""
