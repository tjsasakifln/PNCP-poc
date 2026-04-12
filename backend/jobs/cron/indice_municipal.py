"""STORY-435 AC7: Cron job trimestral — recálculo do Índice Municipal de Transparência."""

import asyncio
import logging
import os
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# Intervalo aproximado de 90 dias (1 trimestre)
INDICE_MUNICIPAL_INTERVAL = 90 * 24 * 60 * 60  # segundos


def _prev_quarter_label() -> str:
    """Retorna o rótulo do trimestre anterior: ex 'YYYY-QN'."""
    now = datetime.now(timezone.utc)
    q = (now.month - 1) // 3 + 1
    if q == 1:
        return f"{now.year - 1}-Q4"
    return f"{now.year}-Q{q - 1}"


async def run_indice_municipal_recalc() -> dict:
    """Executa o recálculo trimestral do Índice Municipal.

    Recalcula todos os municípios do trimestre anterior e envia email summary.
    Nunca lança exceção — erros são capturados e retornados no dict.
    """
    try:
        from services.indice_municipal import recalcular_municipios_existentes

        periodo = _prev_quarter_label()
        logger.info("STORY-435: iniciando recálculo indice_municipal para período %s", periodo)
        result = await recalcular_municipios_existentes(periodo)
        logger.info("STORY-435: recálculo indice_municipal concluído — %s", result)

        # Email summary para admin (falhas de email não abortam o job)
        try:
            from email_service import send_email_async

            admin_email = os.getenv("ADMIN_EMAIL", "tiago.sasaki@gmail.com")
            body_lines = [f"<p>Índice Municipal recalculado para <strong>{periodo}</strong>.</p><ul>"]
            for k, v in result.items():
                body_lines.append(f"<li><strong>{k}</strong>: {v}</li>")
            body_lines.append("</ul>")
            body = "\n".join(body_lines)

            await send_email_async(
                admin_email,
                f"[SmartLic] Índice Municipal {periodo} — recálculo trimestral",
                body,
            )
            logger.info("STORY-435: email summary enviado para %s", admin_email)
        except Exception as email_err:
            logger.warning("STORY-435: falha ao enviar email summary: %s", email_err)

        return result

    except Exception as exc:
        logger.error("STORY-435: recálculo indice_municipal falhou: %s", exc, exc_info=True)
        return {"status": "error", "error": str(exc)}


async def _indice_municipal_loop() -> None:
    """Loop de background: aguarda 90 dias, recalcula, repete."""
    await asyncio.sleep(INDICE_MUNICIPAL_INTERVAL)
    while True:
        try:
            await run_indice_municipal_recalc()
        except asyncio.CancelledError:
            logger.info("STORY-435: indice_municipal task cancelada")
            break
        except Exception as e:
            logger.error("STORY-435: erro inesperado no loop indice_municipal: %s", e, exc_info=True)
        await asyncio.sleep(INDICE_MUNICIPAL_INTERVAL)


async def start_indice_municipal_task() -> asyncio.Task:
    """Cria e retorna a asyncio.Task do loop trimestral."""
    task = asyncio.create_task(
        _indice_municipal_loop(), name="indice_municipal_quarterly"
    )
    logger.info("STORY-435: indice_municipal quarterly recalc task started (interval=90d)")
    return task
