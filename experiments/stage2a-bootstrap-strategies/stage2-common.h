#ifndef CPYTHON_STAGE2_COMMON_H
#define CPYTHON_STAGE2_COMMON_H

#include <Python.h>

#include <dlfcn.h>
#include <errno.h>
#include <limits.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <unistd.h>

#ifndef PATH_MAX
#define PATH_MAX 4096
#endif

struct s2_paths {
    char executable[PATH_MAX];
    char prefix[PATH_MAX];
    char libdir[PATH_MAX];
};

static int
s2_file_exists(const char *path)
{
    struct stat st;
    return stat(path, &st) == 0 && S_ISREG(st.st_mode);
}

static int
s2_copy(char *dst, size_t dst_size, const char *src)
{
    int n = snprintf(dst, dst_size, "%s", src);
    return n >= 0 && (size_t)n < dst_size ? 0 : -1;
}

static int
s2_parent_dir(char *path)
{
    size_t len;

    if (path == NULL || path[0] == '\0') {
        return -1;
    }

    len = strlen(path);

    while (len > 1 && path[len - 1] == '/') {
        path[--len] = '\0';
    }

    while (len > 1 && path[len - 1] != '/') {
        path[--len] = '\0';
    }

    while (len > 1 && path[len - 1] == '/') {
        path[--len] = '\0';
    }

    return 0;
}

static int
s2_discover_paths(struct s2_paths *paths)
{
    ssize_t n;

    memset(paths, 0, sizeof(*paths));

    n = readlink("/proc/self/exe", paths->executable,
                 sizeof(paths->executable) - 1);
    if (n < 0) {
        fprintf(stderr, "stage2: readlink(/proc/self/exe): %s\n",
                strerror(errno));
        return -1;
    }

    paths->executable[n] = '\0';

    if (s2_copy(paths->prefix, sizeof(paths->prefix),
                paths->executable) != 0) {
        fprintf(stderr, "stage2: executable path too long\n");
        return -1;
    }

    /* <prefix>/bin/python-* -> <prefix> */
    if (s2_parent_dir(paths->prefix) != 0 ||
        s2_parent_dir(paths->prefix) != 0) {
        fprintf(stderr, "stage2: cannot derive prefix from %s\n",
                paths->executable);
        return -1;
    }

    if (snprintf(paths->libdir, sizeof(paths->libdir),
                 "%s/lib", paths->prefix) >= (int)sizeof(paths->libdir)) {
        fprintf(stderr, "stage2: libdir path too long\n");
        return -1;
    }

    return 0;
}

static int
s2_prepend_env_path(const char *name, const char *first,
                    char *out, size_t out_size)
{
    const char *old = getenv(name);
    int n;

    if (old != NULL && old[0] != '\0') {
        n = snprintf(out, out_size, "%s:%s", first, old);
    } else {
        n = snprintf(out, out_size, "%s", first);
    }

    if (n < 0 || (size_t)n >= out_size) {
        return -1;
    }

    return setenv(name, out, 1);
}

static int
s2_configure_ca(void)
{
    char candidate[PATH_MAX];
    const char *existing = getenv("SSL_CERT_FILE");
    const char *termux_prefix = getenv("PREFIX");

    if (existing != NULL && existing[0] != '\0') {
        return 0;
    }

    if (termux_prefix != NULL && termux_prefix[0] != '\0') {
        int n = snprintf(candidate, sizeof(candidate),
                         "%s/etc/tls/cert.pem", termux_prefix);
        if (n >= 0 && (size_t)n < sizeof(candidate) &&
            s2_file_exists(candidate)) {
            return setenv("SSL_CERT_FILE", candidate, 1);
        }
    }

    if (s2_file_exists(
            "/data/data/com.termux/files/usr/etc/tls/cert.pem")) {
        return setenv(
            "SSL_CERT_FILE",
            "/data/data/com.termux/files/usr/etc/tls/cert.pem",
            1
        );
    }

    fprintf(stderr,
            "stage2: warning: no Termux CA bundle discovered\n");
    return 0;
}

static int
s2_configure_ld_env(const struct s2_paths *paths,
                    char *combined, size_t combined_size)
{
    if (s2_prepend_env_path(
            "LD_LIBRARY_PATH",
            paths->libdir,
            combined,
            combined_size) != 0) {
        fprintf(stderr,
                "stage2: failed to configure LD_LIBRARY_PATH\n");
        return -1;
    }
    return 0;
}

typedef void (*s2_android_update_ld_library_path_fn)(const char *);
typedef void (*s2_android_get_ld_library_path_fn)(char *, size_t);

static int
s2_update_bionic_linker(const struct s2_paths *paths,
                        char *combined, size_t combined_size)
{
    s2_android_update_ld_library_path_fn update_fn;
    s2_android_get_ld_library_path_fn get_fn;
    char current[PATH_MAX];
    int n;

    dlerror();

    update_fn = (s2_android_update_ld_library_path_fn)
        dlsym(RTLD_DEFAULT, "android_update_LD_LIBRARY_PATH");

    if (update_fn == NULL) {
        const char *err = dlerror();
        fprintf(stderr,
                "stage2: android_update_LD_LIBRARY_PATH unavailable: %s\n",
                err ? err : "unknown error");
        return -1;
    }

    current[0] = '\0';

    get_fn = (s2_android_get_ld_library_path_fn)
        dlsym(RTLD_DEFAULT, "android_get_LD_LIBRARY_PATH");

    if (get_fn != NULL) {
        get_fn(current, sizeof(current));
    }

    if (current[0] != '\0') {
        n = snprintf(combined, combined_size,
                     "%s:%s", paths->libdir, current);
    } else {
        n = snprintf(combined, combined_size,
                     "%s", paths->libdir);
    }

    if (n < 0 || (size_t)n >= combined_size) {
        fprintf(stderr,
                "stage2: linker search path too long\n");
        return -1;
    }

    update_fn(combined);

    /*
     * Keep the process environment consistent for diagnostics and
     * subprocess inheritance. The linker update itself is performed
     * by update_fn above.
     */
    if (setenv("LD_LIBRARY_PATH", combined, 1) != 0) {
        fprintf(stderr,
                "stage2: setenv(LD_LIBRARY_PATH): %s\n",
                strerror(errno));
        return -1;
    }

    return 0;
}

static int
s2_run_pyconfig(int argc, char **argv)
{
    PyConfig config;
    PyStatus status;

    PyConfig_InitPythonConfig(&config);

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

static void
s2_print_diagnostics(const char *variant,
                     const struct s2_paths *paths)
{
    fprintf(stderr,
            "stage2[%s]: executable=%s\n"
            "stage2[%s]: prefix=%s\n"
            "stage2[%s]: libdir=%s\n"
            "stage2[%s]: LD_LIBRARY_PATH=%s\n"
            "stage2[%s]: SSL_CERT_FILE=%s\n",
            variant, paths->executable,
            variant, paths->prefix,
            variant, paths->libdir,
            variant, getenv("LD_LIBRARY_PATH")
                         ? getenv("LD_LIBRARY_PATH") : "<unset>",
            variant, getenv("SSL_CERT_FILE")
                         ? getenv("SSL_CERT_FILE") : "<unset>");
}

#endif
