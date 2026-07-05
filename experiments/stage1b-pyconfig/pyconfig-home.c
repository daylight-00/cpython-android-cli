/*
 * Stage 1-B / B1 explicit-home launcher
 *
 * Purpose:
 *   Follow the initialization shape used by CPython's Android testbed:
 *
 *     PyConfig_InitPythonConfig
 *     PyConfig_SetBytesArgv
 *     PyConfig_SetBytesString(config.home)
 *     Py_InitializeFromConfig
 *     Py_RunMain
 *
 * CPYTHON_HOME is deliberately a project-specific experiment variable.
 * It is not part of the frozen Stage 1-A runtime contract.
 *
 * Runtime integration remains external:
 *   LD_LIBRARY_PATH=<cpython-prefix>/lib
 *   SSL_CERT_FILE=<termux-prefix>/etc/tls/cert.pem
 */

#include <Python.h>

#include <stdio.h>
#include <stdlib.h>

int
main(int argc, char **argv)
{
    const char *home;
    PyConfig config;
    PyStatus status;

    home = getenv("CPYTHON_HOME");
    if (home == NULL || home[0] == '\0') {
        fprintf(
            stderr,
            "python-pyconfig-home: CPYTHON_HOME is not set\n"
        );
        return 64;
    }

    PyConfig_InitPythonConfig(&config);

    /*
     * Keep the same ordering as the upstream Android testbed:
     * argv first, then home.
     */
    status = PyConfig_SetBytesArgv(&config, argc, argv);
    if (PyStatus_Exception(status)) {
        goto exception;
    }

    status = PyConfig_SetBytesString(&config, &config.home, home);
    if (PyStatus_Exception(status)) {
        goto exception;
    }

    status = Py_InitializeFromConfig(&config);
    if (PyStatus_Exception(status)) {
        goto exception;
    }

    PyConfig_Clear(&config);
    return Py_RunMain();

exception:
    PyConfig_Clear(&config);

    if (PyStatus_IsExit(status)) {
        return status.exitcode;
    }

    Py_ExitStatusException(status);
}
