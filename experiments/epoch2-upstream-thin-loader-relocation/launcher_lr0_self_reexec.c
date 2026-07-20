#include <Python.h>
#include <errno.h>
#include <limits.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#ifndef PATH_MAX
#define PATH_MAX 4096
#endif

static int parent(char *p) {
    size_t n = strlen(p);
    while (n > 1 && p[n - 1] == '/') p[--n] = 0;
    while (n > 1 && p[n - 1] != '/') p[--n] = 0;
    while (n > 1 && p[n - 1] == '/') p[--n] = 0;
    return n > 0 ? 0 : -1;
}

static int contains_component(const char *list, const char *wanted) {
    const char *s, *p;
    size_t wn = strlen(wanted);
    if (!list || !*list) return 0;
    s = list;
    for (p = list;; p++) {
        if (*p == ':' || *p == 0) {
            if ((size_t)(p - s) == wn && memcmp(s, wanted, wn) == 0) return 1;
            if (*p == 0) break;
            s = p + 1;
        }
    }
    return 0;
}

static int run_pyconfig(int argc, char **argv) {
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

int main(int argc, char **argv) {
    char exe[PATH_MAX], prefix[PATH_MAX], libdir[PATH_MAX], value[PATH_MAX * 4];
    const char *old;
    ssize_t n = readlink("/proc/self/exe", exe, sizeof(exe) - 1);
    if (n < 0) { perror("readlink(/proc/self/exe)"); return 70; }
    exe[n] = 0;
    if (snprintf(prefix, sizeof(prefix), "%s", exe) >= (int)sizeof(prefix)) return 71;
    if (parent(prefix) || parent(prefix)) return 72;
    if (snprintf(libdir, sizeof(libdir), "%s/lib", prefix) >= (int)sizeof(libdir)) return 73;
    old = getenv("LD_LIBRARY_PATH");
    if (!contains_component(old, libdir)) {
        if (old && *old) {
            if (snprintf(value, sizeof(value), "%s:%s", libdir, old) >= (int)sizeof(value)) return 74;
        } else {
            if (snprintf(value, sizeof(value), "%s", libdir) >= (int)sizeof(value)) return 74;
        }
        if (setenv("LD_LIBRARY_PATH", value, 1) != 0) return 75;
        if (setenv("HW_T_LR0_SELF_REEXEC", "1", 1) != 0) return 76;
        execv(exe, argv);
        perror("execv");
        return 77;
    }
    return run_pyconfig(argc, argv);
}
