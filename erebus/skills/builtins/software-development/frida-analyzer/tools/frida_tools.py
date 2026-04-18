"""Frida dynamic instrumentation tools for CodeAgent.

Requires: pip install frida-tools
          adb on PATH for Android targets

Provides mobile app analysis, SSL unpinning, and runtime hooking.
"""

from __future__ import annotations

import subprocess
from typing import Any


def _run(cmd: list[str], timeout: int = 30) -> str:
    """Run a command and return output."""
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout,
        )
        out = result.stdout.strip()
        err = result.stderr.strip()
        return out + ("\n" + err if err else "") or "(no output)"
    except FileNotFoundError:
        return f"Command not found: {cmd[0]} — install frida-tools"
    except subprocess.TimeoutExpired:
        return f"Command timed out after {timeout}s"
    except Exception as exc:
        return f"Error: {exc}"


def frida_devices() -> str:
    """List connected Frida devices.

    Returns
    -------
    str
        Device list.
    """
    return _run(["frida-ls-devices"])


def frida_apps(device: str = "usb") -> list[str]:
    """List installed apps on a Frida device.

    Parameters
    ----------
    device:
        Device type: ``"usb"``, ``"local"``, or device ID.

    Returns
    -------
    list[str]
        App identifiers.
    """
    flag = "-U" if device == "usb" else "-D" if device == "local" else f"-D {device}"
    output = _run(["frida-ps", flag, "-ai"])
    return output.split("\n")


def frida_spawn(
    package: str,
    script: str | None = None,
    device: str = "usb",
) -> str:
    """Spawn an app with optional Frida script.

    Parameters
    ----------
    package:
        App package name (e.g. ``"com.example.app"``).
    script:
        Path to a Frida JS script file.
    device:
        Device identifier.

    Returns
    -------
    str
        Spawn result.
    """
    flag = "-U" if device == "usb" else f"-D {device}"
    cmd = ["frida", flag, "-f", package, "--no-pause"]
    if script:
        cmd.extend(["-l", script])
    return _run(cmd, timeout=15)


def frida_attach(
    target: str,
    script: str | None = None,
    device: str = "usb",
) -> str:
    """Attach to a running process.

    Parameters
    ----------
    target:
        Process name or PID.
    script:
        Path to a Frida JS script file.
    device:
        Device identifier.

    Returns
    -------
    str
        Attach result.
    """
    flag = "-U" if device == "usb" else f"-D {device}"
    cmd = ["frida", flag, target]
    if script:
        cmd.extend(["-l", script])
    return _run(cmd, timeout=15)


# SSL unpinning script (based on httptoolkit/frida-interception-and-unpinning)
_UNPIN_SCRIPT = r"""
Java.perform(function() {
    // TrustManager bypass
    var TrustManagerImpl = Java.use(
        'com.android.org.conscrypt.TrustManagerImpl'
    );
    if (TrustManagerImpl) {
        TrustManagerImpl.verifyChain.implementation = function() {
            console.log('[*] SSL pin bypassed (TrustManagerImpl)');
            return arguments[0];
        };
    }

    // OkHttp CertificatePinner bypass
    try {
        var CertPinner = Java.use('okhttp3.CertificatePinner');
        CertPinner.check.overload('java.lang.String', 'java.util.List')
            .implementation = function() {
            console.log('[*] OkHttp pin bypassed');
        };
    } catch(e) {}

    console.log('[*] SSL unpinning hooks installed');
});
"""


def frida_unpin_ssl(package: str, device: str = "usb") -> str:
    """Bypass SSL pinning on an Android app.

    Spawns the app with an SSL unpinning Frida script based on
    httptoolkit/frida-interception-and-unpinning.

    Parameters
    ----------
    package:
        App package name.
    device:
        Device identifier.

    Returns
    -------
    str
        Result.
    """
    import os
    import tempfile

    script_path = os.path.join(
        tempfile.mkdtemp(prefix="frida_unpin_"), "unpin.js"
    )
    with open(script_path, "w") as f:
        f.write(_UNPIN_SCRIPT)
    return frida_spawn(package, script=script_path, device=device)


def frida_trace(
    package: str,
    pattern: str,
    device: str = "usb",
) -> str:
    """Trace function calls matching a pattern.

    Parameters
    ----------
    package:
        App package name.
    pattern:
        Method pattern to trace (e.g. ``"*!open*"``).
    device:
        Device identifier.

    Returns
    -------
    str
        Trace output.
    """
    flag = "-U" if device == "usb" else f"-D {device}"
    return _run(
        ["frida-trace", flag, "-i", pattern, "-f", package],
        timeout=20,
    )


def frida_run_script(
    target: str,
    script_code: str,
    device: str = "usb",
) -> str:
    """Inject and run custom JavaScript via Frida.

    Parameters
    ----------
    target:
        Process name or package.
    script_code:
        Frida JavaScript code.
    device:
        Device identifier.

    Returns
    -------
    str
        Script output.
    """
    import os
    import tempfile

    script_path = os.path.join(
        tempfile.mkdtemp(prefix="frida_script_"), "script.js"
    )
    with open(script_path, "w") as f:
        f.write(script_code)
    flag = "-U" if device == "usb" else f"-D {device}"
    return _run(
        ["frida", flag, "-f", target, "-l", script_path, "--no-pause"],
        timeout=20,
    )


# -- TOOLS dict: required export for CodeAgent skill tool loading --
TOOLS: dict[str, Any] = {
    "frida_devices": frida_devices,
    "frida_apps": frida_apps,
    "frida_spawn": frida_spawn,
    "frida_attach": frida_attach,
    "frida_unpin_ssl": frida_unpin_ssl,
    "frida_trace": frida_trace,
    "frida_run_script": frida_run_script,
}
