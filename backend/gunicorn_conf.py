"""CRIT-034: Gunicorn configuration with worker lifecycle hooks.

This config file is loaded by gunicorn via the -c flag in start.sh.
It defines ONLY hooks (not settings like workers/timeout/bind — those
are set via CLI args in start.sh so they can be env-var-overridden).

Hooks:
    post_worker_init: Installs SIGABRT handler in each worker for
                      structured timeout logging (AC7) + Sentry (AC5).
    worker_abort:     Arbiter-side logging when killing a timed-out worker.
"""

import logging

logger = logging.getLogger("gunicorn.conf")


def post_worker_init(worker):
    """Install SIGABRT handler in worker for structured timeout diagnostics.

    Called by gunicorn after a worker process has been initialized.
    Runs in the WORKER process context (not the arbiter).
    """
    try:
        from worker_lifecycle import install_timeout_handler
        install_timeout_handler(worker.pid)
    except Exception as e:
        logger.warning(f"CRIT-034: Failed to install timeout handler: {e}")


def worker_abort(worker):
    """Log worker timeout in the arbiter + capture to Sentry.

    Called by gunicorn arbiter when sending SIGABRT to a timed-out worker.
    Runs in the ARBITER process context (not the worker).

    Note: The worker's own SIGABRT handler (installed via post_worker_init)
    provides request-level context (endpoint, search_id, duration). This
    arbiter-side hook provides a second signal with worker metadata.
    """
    logger.critical(
        f"WORKER TIMEOUT — arbiter killing worker | pid={worker.pid}"
    )
    try:
        import sentry_sdk
        with sentry_sdk.new_scope() as scope:
            scope.set_tag("worker.pid", str(worker.pid))
            scope.set_tag("source", "gunicorn_arbiter")
            scope.set_level("fatal")
            sentry_sdk.capture_message(
                f"WORKER TIMEOUT (pid:{worker.pid}) — killed by arbiter",
            )
    except Exception:
        pass


def worker_exit(server, worker):
    """SLA-002: Log worker exit with reason for OOM/crash diagnosis.

    Called by gunicorn arbiter when a worker exits (clean or crash).
    Tracks exit codes to identify OOM kills (code -9) vs normal recycling.
    """
    exit_code = worker.exitcode if hasattr(worker, "exitcode") else "unknown"
    if exit_code == -9:
        logger.critical(
            f"WORKER OOM KILLED — pid={worker.pid} exit_code={exit_code} "
            f"(likely out of memory — consider reducing WEB_CONCURRENCY)"
        )
    elif exit_code == 0:
        logger.info(
            f"Worker recycled cleanly — pid={worker.pid} (max-requests reached)"
        )
    else:
        logger.warning(
            f"Worker exited — pid={worker.pid} exit_code={exit_code}"
        )
