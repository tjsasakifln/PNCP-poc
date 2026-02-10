"""
Message Generator - Create personalized outreach messages using OpenAI.

This module generates personalized sales messages based on:
- Company data
- Recent contract wins
- Sector alignment
- Strategic intelligence

STORY-184: Lead Prospecting Workflow
"""

import logging
from typing import Optional, List
import os

import openai
from openai import OpenAI

from schemas_lead_prospecting import (
    LeadProfile,
    ContractData,
    CompanyData,
    StrategicIntelligence,
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
        dependency_percentage: float,
    ) -> str:
        """
        Generate personalized outreach message.

        Args:
            company_name: Company name
            sector: Primary sector
            recent_contract: Most recent contract win
            intelligence: Strategic intelligence
            dependency_percentage: Dependency score (%)

        Returns:
            Personalized message (plain text)
        """
        if not self.client:
            return self._fallback_message(company_name, sector, recent_contract)

        # Build prompt
        system_prompt = """Você é um especialista em vendas B2B no setor de licitações públicas.
Sua tarefa é criar emails personalizados de prospecção para empresas que participam de licitações.

Requisitos:
- Tom profissional mas caloroso
- Referenciar contrato recente específico
- Mencionar valor do SmartLic (descoberta automática de oportunidades)
- Oferecer valor imediato (planilha anexa com oportunidades)
- Call to action: agendar 15 minutos
- Máximo 150 palavras
- NÃO incluir assunto (subject line)"""

        user_prompt = f"""Empresa: {company_name}
Setor: {sector}
Contrato Recente: {recent_contract.contract_object[:200]} (R$ {recent_contract.contract_value:,.2f})
Data: {recent_contract.contract_date}
Inteligência: {intelligence.summary[:300]}
Dependência de Licitações: {dependency_percentage:.0f}%

Crie um email personalizado de apresentação do SmartLic."""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4-turbo-preview",
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
            return self._fallback_message(company_name, sector, recent_contract)

    def _fallback_message(
        self, company_name: str, sector: str, recent_contract: ContractData
    ) -> str:
        """
        Generate fallback message without OpenAI (template-based).

        Args:
            company_name: Company name
            sector: Primary sector
            recent_contract: Most recent contract win

        Returns:
            Template-based message
        """
        return f"""Olá, equipe da {company_name}!

Parabéns pelo contrato recente em {sector} (R$ {recent_contract.contract_value:,.2f})!

Identificamos várias oportunidades abertas em {sector} que se alinham perfeitamente com o histórico de atuação da {company_name}.

Preparei uma planilha com essas oportunidades (anexo), incluindo licitações abertas em diversos estados.

O SmartLic automatiza a busca de licitações em todo o Brasil, filtrando por setor, região e valor. Empresas como a {company_name} economizam horas de prospecção manual.

Podemos agendar 15 minutos para eu apresentar outras oportunidades que identificamos especificamente para vocês?

Atenciosamente,
[Seu Nome]
SmartLic
[Seu Contato]"""
