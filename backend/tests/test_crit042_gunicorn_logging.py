"""Tests for CRIT-044: Gunicorn logconfig_dict — stderr → stdout redirect.

Root cause: Gunicorn writes all internal logs (including INFO) to stderr.
Railway classifies stderr as severity=error. Fix: logconfig_dict redirects
gunicorn.error, gunicorn.access, gunicorn.conf to stdout with JSON format
containing a "level" field for correct Railway severity classification.
"""

import io
import json
import logging
import logging.config
from unittest.mock import patch



class TestLogconfigDictStructure:
    """Verify logconfig_dict has the correct structure for Gunicorn."""

    def test_logconfig_dict_exists(self):
        """logconfig_dict is defined and is a valid dictConfig."""
        with patch.dict("os.environ", {"ENVIRONMENT": "production"}, clear=False):
            import importlib
            import gunicorn_conf
            importlib.reload(gunicorn_conf)
            assert hasattr(gunicorn_conf, "logconfig_dict")
            assert isinstance(gunicorn_conf.logconfig_dict, dict)
            assert gunicorn_conf.logconfig_dict["version"] == 1

    def test_disable_existing_loggers_false(self):
        """Must not disable existing loggers (app logging via config.py)."""
        with patch.dict("os.environ", {"ENVIRONMENT": "production"}, clear=False):
            import importlib
            import gunicorn_conf
            importlib.reload(gunicorn_conf)
            assert gunicorn_conf.logconfig_dict["disable_existing_loggers"] is False

    def test_all_gunicorn_loggers_configured(self):
        """gunicorn.error, gunicorn.access, gunicorn.conf must be redirected."""
        with patch.dict("os.environ", {"ENVIRONMENT": "production"}, clear=False):
            import importlib
            import gunicorn_conf
            importlib.reload(gunicorn_conf)
            loggers = gunicorn_conf.logconfig_dict["loggers"]
            for name in ("gunicorn.error", "gunicorn.access", "gunicorn.conf"):
                assert name in loggers, f"Missing logger: {name}"
                assert "stdout" in loggers[name]["handlers"]
                assert loggers[name]["propagate"] is False

    def test_handler_uses_stdout(self):
        """Handler stream must be stdout, not stderr."""
        with patch.dict("os.environ", {"ENVIRONMENT": "production"}, clear=False):
            import importlib
            import gunicorn_conf
            importlib.reload(gunicorn_conf)
            handler = gunicorn_conf.logconfig_dict["handlers"]["stdout"]
            assert handler["stream"] == "ext://sys.stdout"


class TestJsonFormatterProduction:
    """In production, logs must be JSON with a 'level' field for Railway."""

    def test_json_formatter_in_production(self):
        """Production env uses pythonjsonlogger.jsonlogger.JsonFormatter."""
        with patch.dict("os.environ", {"ENVIRONMENT": "production"}, clear=False):
            import importlib
            import gunicorn_conf
            importlib.reload(gunicorn_conf)
            fmt = gunicorn_conf.logconfig_dict["formatters"]["gunicorn_fmt"]
            assert "()" in fmt
            assert "JsonFormatter" in fmt["()"]

    def test_rename_fields_includes_level(self):
        """rename_fields must map levelname → level (Railway reads this)."""
        with patch.dict("os.environ", {"ENVIRONMENT": "production"}, clear=False):
            import importlib
            import gunicorn_conf
            importlib.reload(gunicorn_conf)
            fmt = gunicorn_conf.logconfig_dict["formatters"]["gunicorn_fmt"]
            assert fmt["rename_fields"]["levelname"] == "level"

    def test_json_output_has_level_field(self):
        """Applying logconfig_dict produces JSON with 'level' field on stdout."""
        with patch.dict("os.environ", {"ENVIRONMENT": "production"}, clear=False):
            import importlib
            import gunicorn_conf
            importlib.reload(gunicorn_conf)

            # Capture stdout
            buf = io.StringIO()

            # Apply the dictConfig
            logging.config.dictConfig(gunicorn_conf.logconfig_dict)

            # Redirect the stdout handler to our buffer
            gc_logger = logging.getLogger("gunicorn.error")
            for h in gc_logger.handlers:
                if isinstance(h, logging.StreamHandler):
                    h.stream = buf

            gc_logger.info("Test startup message")

            output = buf.getvalue().strip()
            assert output, "No log output captured"
            parsed = json.loads(output)
            assert "level" in parsed
            assert parsed["level"] == "INFO"
            assert parsed["message"] == "Test startup message"

    def test_json_output_has_timestamp(self):
        """JSON output must include timestamp field."""
        with patch.dict("os.environ", {"ENVIRONMENT": "production"}, clear=False):
            import importlib
            import gunicorn_conf
            importlib.reload(gunicorn_conf)

            buf = io.StringIO()
            logging.config.dictConfig(gunicorn_conf.logconfig_dict)
            gc_logger = logging.getLogger("gunicorn.error")
            for h in gc_logger.handlers:
                if isinstance(h, logging.StreamHandler):
                    h.stream = buf

            gc_logger.info("Timestamp test")
            parsed = json.loads(buf.getvalue().strip())
            assert "timestamp" in parsed


class TestTextFormatterDevelopment:
    """In development, logs use human-readable text format on stdout."""

    def test_text_formatter_in_development(self):
        """Development env uses standard text formatter (no '()' factory)."""
        with patch.dict("os.environ", {"ENVIRONMENT": "development"}, clear=False):
            import importlib
            import gunicorn_conf
            importlib.reload(gunicorn_conf)
            fmt = gunicorn_conf.logconfig_dict["formatters"]["gunicorn_fmt"]
            assert "()" not in fmt
            assert "format" in fmt

    def test_text_output_on_stdout(self):
        """Development text logs still go to stdout (not stderr)."""
        with patch.dict("os.environ", {"ENVIRONMENT": "development"}, clear=False):
            import importlib
            import gunicorn_conf
            importlib.reload(gunicorn_conf)

            buf = io.StringIO()
            logging.config.dictConfig(gunicorn_conf.logconfig_dict)
            gc_logger = logging.getLogger("gunicorn.conf")
            for h in gc_logger.handlers:
                if isinstance(h, logging.StreamHandler):
                    h.stream = buf

            gc_logger.info("Dev test")
            output = buf.getvalue()
            assert "Dev test" in output
            assert "INFO" in output


class TestLogFormatEnvOverride:
    """LOG_FORMAT env var overrides auto-detection."""

    def test_log_format_json_forces_json(self):
        """LOG_FORMAT=json in dev env still uses JSON formatter."""
        with patch.dict("os.environ", {"ENVIRONMENT": "development", "LOG_FORMAT": "json"}, clear=False):
            import importlib
            import gunicorn_conf
            importlib.reload(gunicorn_conf)
            fmt = gunicorn_conf.logconfig_dict["formatters"]["gunicorn_fmt"]
            assert "()" in fmt

    def test_log_format_text_forces_text(self):
        """LOG_FORMAT=text in prod env still uses text formatter."""
        with patch.dict("os.environ", {"ENVIRONMENT": "production", "LOG_FORMAT": "text"}, clear=False):
            import importlib
            import gunicorn_conf
            importlib.reload(gunicorn_conf)
            fmt = gunicorn_conf.logconfig_dict["formatters"]["gunicorn_fmt"]
            assert "()" not in fmt


class TestHooksStillWork:
    """Existing lifecycle hooks must not regress."""

    def test_when_ready_uses_gunicorn_conf_logger(self):
        """when_ready hook logs via gunicorn.conf logger (redirected to stdout)."""
        import importlib
        import gunicorn_conf
        importlib.reload(gunicorn_conf)

        # Mock server object
        class MockServer:
            pid = 1234
            num_workers = 2
            class cfg:
                preload_app = False

        buf = io.StringIO()
        logging.config.dictConfig(gunicorn_conf.logconfig_dict)
        gc_logger = logging.getLogger("gunicorn.conf")
        for h in gc_logger.handlers:
            if isinstance(h, logging.StreamHandler):
                h.stream = buf

        gunicorn_conf.when_ready(MockServer())
        output = buf.getvalue()
        assert "STORY-303" in output
        assert "workers=2" in output

    def test_worker_exit_clean(self):
        """worker_exit with code 0 logs at INFO level."""
        import importlib
        import gunicorn_conf
        importlib.reload(gunicorn_conf)

        class MockServer:
            pass

        class MockWorker:
            pid = 42
            exitcode = 0

        buf = io.StringIO()
        logging.config.dictConfig(gunicorn_conf.logconfig_dict)
        gc_logger = logging.getLogger("gunicorn.conf")
        for h in gc_logger.handlers:
            if isinstance(h, logging.StreamHandler):
                h.stream = buf

        gunicorn_conf.worker_exit(MockServer(), MockWorker())
        output = buf.getvalue()
        assert "recycled cleanly" in output
