"""Gunicorn configuration with worker lifecycle hooks.

This config file is loaded by gunicorn via the -c flag in start.sh.
It defines ONLY hooks (not settings like workers/timeout/bind — those
are set via CLI args in start.sh so they can be env-var-overridden).

Hooks:
    when_ready:       STORY-303 AC5 — Logs readiness after workers spawned.
    post_worker_init: CRIT-034 — Installs SIGABRT handler in each worker for
                      structured timeout logging + Sentry.
    worker_abort:     CRIT-034 — Arbiter-side logging when killing a timed-out worker.
    worker_exit:      SLA-002 + STORY-303 AC15 — Logs worker exit with crash diagnosis
                      (SIGSEGV -11, OOM -9, other non-zero).
"""

import logging

logger = logging.getLogger("gunicorn.conf")


def when_ready(server):
    """STORY-303 AC5: Log readiness after all workers have been spawned.

    Combined with Railway healthcheckTimeout=300s, this ensures traffic is only
    routed after workers are fully initialized — mitigating CRIT-010 404s
    without needing --preload (which causes SIGSEGV with cryptography).
    """
    logger.info(
        f"STORY-303: All workers ready — master pid={server.pid}, "
        f"workers={server.num_workers}, preload={'ON' if server.cfg.preload_app else 'OFF'}"
    )


def post_worker_init(worker):
    """Install SIGABRT handler + faulthandler in worker for crash diagnostics.

    Called by gunicorn after a worker process has been initialized.
    Runs in the WORKER process context (not the arbiter).
    """
    # CRIT-041: Enable faulthandler in EACH worker process.
    # main.py enables it at import time, but without --preload the master
    # doesn't import main.py — so faulthandler may not be active in workers
    # that crash before importing main. This guarantees it's always on.
    import faulthandler
    if not faulthandler.is_enabled():
        faulthandler.enable()
        logger.info(f"CRIT-041: faulthandler enabled in worker pid={worker.pid}")

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
    """SLA-002 + STORY-303 AC15/AC16: Log worker exit with crash diagnosis.

    Called by gunicorn arbiter when a worker exits (clean or crash).
    Tracks exit codes to identify:
      -11 (SIGSEGV): Segfault — likely cryptography/OpenSSL fork-safety issue
       -9 (SIGKILL): OOM kill
        0: Normal recycling (max-requests)
      Any other non-zero: Unexpected crash
    """
    exit_code = worker.exitcode if hasattr(worker, "exitcode") else "unknown"

    # STORY-303 AC15: SIGSEGV detection (exit code -11 = signal 11)
    if exit_code == -11:
        logger.critical(
            f"WORKER SIGSEGV — pid={worker.pid} exit_code={exit_code} "
            f"(segmentation fault — check cryptography fork-safety, "
            f"verify GUNICORN_PRELOAD=false)"
        )
        try:
            import sentry_sdk
            with sentry_sdk.new_scope() as scope:
                scope.set_tag("worker.pid", str(worker.pid))
                scope.set_tag("exit_code", str(exit_code))
                scope.set_tag("crash_type", "SIGSEGV")
                scope.set_tag("source", "gunicorn_worker_exit")
                scope.set_level("fatal")
                sentry_sdk.capture_message(
                    f"WORKER SIGSEGV (pid:{worker.pid}) — segmentation fault, "
                    f"check cryptography fork-safety",
                )
        except Exception:
            pass
    elif exit_code == -9:
        logger.critical(
            f"WORKER OOM KILLED — pid={worker.pid} exit_code={exit_code} "
            f"(likely out of memory — consider reducing WEB_CONCURRENCY)"
        )
        try:
            import sentry_sdk
            with sentry_sdk.new_scope() as scope:
                scope.set_tag("worker.pid", str(worker.pid))
                scope.set_tag("exit_code", str(exit_code))
                scope.set_tag("crash_type", "OOM")
                scope.set_tag("source", "gunicorn_worker_exit")
                scope.set_level("fatal")
                sentry_sdk.capture_message(
                    f"WORKER OOM KILLED (pid:{worker.pid})",
                )
        except Exception:
            pass
    elif exit_code == 0:
        logger.info(
            f"Worker recycled cleanly — pid={worker.pid} (max-requests reached)"
        )
    # STORY-303 AC16: ALL non-zero exit codes logged
    else:
        logger.warning(
            f"Worker exited unexpectedly — pid={worker.pid} exit_code={exit_code}"
        )
        try:
            import sentry_sdk
            with sentry_sdk.new_scope() as scope:
                scope.set_tag("worker.pid", str(worker.pid))
                scope.set_tag("exit_code", str(exit_code))
                scope.set_tag("crash_type", "unexpected")
                scope.set_tag("source", "gunicorn_worker_exit")
                scope.set_level("error")
                sentry_sdk.capture_message(
                    f"WORKER UNEXPECTED EXIT (pid:{worker.pid}) code={exit_code}",
                )
        except Exception:
            pass
