#include <Python.h>

int main(int argc, char **argv) {
    PyConfig config;
    PyStatus status;
    PyConfig_InitPythonConfig(&config);
    status = PyConfig_SetBytesArgv(&config, argc, argv);
    if (PyStatus_Exception(status)) goto exception;
    status = Py_InitializeFromConfig(&config);
    if (PyStatus_Exception(status)) goto exception;
    PyConfig_Clear(&config);
    return Py_RunMain();
exception:
    PyConfig_Clear(&config);
    if (PyStatus_IsExit(status)) return status.exitcode;
    Py_ExitStatusException(status);
}
