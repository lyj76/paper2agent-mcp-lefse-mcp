"""rpy2 3.x -> 2.x assignment-visibility compatibility shim.

LEfSe's upstream scripts (lefse.py, lefse_run.py) call
``rpy2.robjects.r("x <- <expr>")`` and use the *returned* value.  rpy2 3.x
returns ``None`` for an invisible assignment (``x <- <expr>`` is invisible in
R), whereas the rpy2 2.x behavior LEfSe targets returned the assigned object.
This module is imported automatically by the interpreter at startup
(sitecustomize) inside the LEfSe CLI subprocesses launched by the wrapper, and
simply wraps every ``r(...)`` string in parentheses so the assigned value is
returned.  The R computation executed upstream is byte-for-byte identical; only
the Python-side visibility of assignments is normalized.  It does not touch the
frozen upstream source.
"""
from __future__ import annotations


def _install() -> None:
    try:
        import rpy2.robjects as ro
    except Exception:  # pragma: no cover - rpy2 should be present in this env
        return

    original = ro.r

    def visible_r(code, *args, **kwargs):
        if isinstance(code, str):
            stripped = code.strip()
            return original("(" + stripped + ")", *args, **kwargs)
        return original(code, *args, **kwargs)

    ro.r = visible_r


_install()