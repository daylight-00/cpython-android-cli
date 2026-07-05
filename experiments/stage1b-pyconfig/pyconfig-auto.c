/*
 * Stage 1-B / B0 control launcher
 *
 * Purpose:
 *   Replace Py_BytesMain with the explicit PyConfig initialization path,
 *   while leaving Python path discovery untouched.
 *
 * Runtime integration remains external, as frozen in Stage 1-A:
 *   LD_LIBRARY_PATH=<cpython-prefix>/lib
 *   SSL_CERT_FILE=<termux-prefix>/etc/tls/cert.pem
 */

#include <Python.h>

int
main(int argc, char **argv)
{
    PyConfig config;
    PyStatus status;

    PyConfig_InitPythonConfig(&config);

    /*
     * PyConfig_SetBytesArgv must run before other PyConfig methods when
     * command-line parsing is enabled, because it may preinitialize Python.
     */
    status = PyConfig_SetBytesArgv(&config, argc, argv);
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
