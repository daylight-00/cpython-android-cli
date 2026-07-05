#ifndef CPYTHON_STAGE2B_COMMON_H
#define CPYTHON_STAGE2B_COMMON_H

#include <Python.h>

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

struct s2b_paths {
    char executable[PATH_MAX];
    char prefix[PATH_MAX];
    char libdir[PATH_MAX];
};

static int
s2b_is_regular_file(const char *path)
{
    struct stat st;

    if (path == NULL || path[0] == '\0') {
        return 0;
    }

    return stat(path, &st) == 0 && S_ISREG(st.st_mode);
}

static int
s2b_copy(char *dst, size_t dst_size, const char *src)
{
    int n = snprintf(dst, dst_size, "%s", src);
    return n >= 0 && (size_t)n < dst_size ? 0 : -1;
}

static int
s2b_parent_dir(char *path)
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
s2b_discover_paths(struct s2b_paths *paths)
{
    ssize_t n;

    memset(paths, 0, sizeof(*paths));

    n = readlink(
        "/proc/self/exe",
        paths->executable,
        sizeof(paths->executable) - 1
    );

    if (n < 0) {
        fprintf(
            stderr,
            "stage2b: readlink(/proc/self/exe): %s\n",
            strerror(errno)
        );
        return -1;
    }

    paths->executable[n] = '\0';

    if (s2b_copy(
            paths->prefix,
            sizeof(paths->prefix),
            paths->executable) != 0) {
        fprintf(stderr, "stage2b: executable path too long\n");
        return -1;
    }

    /* <prefix>/bin/<launcher> -> <prefix> */
    if (s2b_parent_dir(paths->prefix) != 0 ||
        s2b_parent_dir(paths->prefix) != 0) {
        fprintf(
            stderr,
            "stage2b: cannot derive prefix from %s\n",
            paths->executable
        );
        return -1;
    }

    if (snprintf(
            paths->libdir,
            sizeof(paths->libdir),
            "%s/lib",
            paths->prefix) >= (int)sizeof(paths->libdir)) {
        fprintf(stderr, "stage2b: libdir path too long\n");
        return -1;
    }

    return 0;
}

static int
s2b_component_equals(
    const char *start,
    size_t length,
    const char *wanted
)
{
    size_t wanted_len = strlen(wanted);
    return length == wanted_len &&
           memcmp(start, wanted, length) == 0;
}

static int
s2b_path_list_contains(const char *list, const char *wanted)
{
    const char *p;
    const char *start;

    if (list == NULL || list[0] == '\0') {
        return 0;
    }

    start = list;

    for (p = list; ; p++) {
        if (*p == ':' || *p == '\0') {
            size_t len = (size_t)(p - start);

            if (s2b_component_equals(start, len, wanted)) {
                return 1;
            }

            if (*p == '\0') {
                break;
            }

            start = p + 1;
        }
    }

    return 0;
}

/*
 * Ensure WANTED occurs exactly once in LIST.
 *
 * - If absent, prepend it.
 * - If duplicated, keep the first occurrence and remove later copies.
 * - Preserve the order of all other components.
 *
 * Empty path components are preserved.
 */
static int
s2b_normalize_required_path(
    const char *list,
    const char *wanted,
    char *out,
    size_t out_size,
    int *was_present
)
{
    const char *p;
    const char *start;
    size_t used = 0;
    int found = 0;
    int first_output_component = 1;

#define APPEND_BYTES(ptr, count)                                         \
    do {                                                                  \
        size_t _count = (count);                                          \
        if (used + _count + 1 > out_size) {                               \
            return -1;                                                    \
        }                                                                 \
        memcpy(out + used, (ptr), _count);                                \
        used += _count;                                                   \
        out[used] = '\0';                                                 \
    } while (0)

#define APPEND_SEPARATOR_IF_NEEDED()                                      \
    do {                                                                  \
        if (!first_output_component) {                                    \
            APPEND_BYTES(":", 1);                                         \
        }                                                                 \
        first_output_component = 0;                                       \
    } while (0)

    if (list == NULL || list[0] == '\0') {
        if (snprintf(out, out_size, "%s", wanted) >= (int)out_size) {
            return -1;
        }
        *was_present = 0;
        return 0;
    }

    start = list;

    for (p = list; ; p++) {
        if (*p == ':' || *p == '\0') {
            size_t len = (size_t)(p - start);
            int is_wanted = s2b_component_equals(start, len, wanted);

            if (is_wanted) {
                if (!found) {
                    APPEND_SEPARATOR_IF_NEEDED();
                    APPEND_BYTES(start, len);
                    found = 1;
                }
            } else {
                APPEND_SEPARATOR_IF_NEEDED();
                APPEND_BYTES(start, len);
            }

            if (*p == '\0') {
                break;
            }

            start = p + 1;
        }
    }

    if (!found) {
        char preserved[PATH_MAX * 4];

        if (s2b_copy(preserved, sizeof(preserved), out) != 0) {
            return -1;
        }

        if (preserved[0] != '\0') {
            if (snprintf(
                    out,
                    out_size,
                    "%s:%s",
                    wanted,
                    preserved) >= (int)out_size) {
                return -1;
            }
        } else {
            if (snprintf(out, out_size, "%s", wanted) >= (int)out_size) {
                return -1;
            }
        }
    }

    *was_present = found;

#undef APPEND_SEPARATOR_IF_NEEDED
#undef APPEND_BYTES

    return 0;
}

static int
s2b_configure_ca(char *selected, size_t selected_size)
{
    char candidate[PATH_MAX];
    const char *existing = getenv("SSL_CERT_FILE");
    const char *termux_prefix = getenv("PREFIX");

    if (s2b_is_regular_file(existing)) {
        return s2b_copy(selected, selected_size, existing);
    }

    if (termux_prefix != NULL && termux_prefix[0] != '\0') {
        int n = snprintf(
            candidate,
            sizeof(candidate),
            "%s/etc/tls/cert.pem",
            termux_prefix
        );

        if (n >= 0 &&
            (size_t)n < sizeof(candidate) &&
            s2b_is_regular_file(candidate)) {
            if (setenv("SSL_CERT_FILE", candidate, 1) != 0) {
                return -1;
            }
            return s2b_copy(selected, selected_size, candidate);
        }
    }

    if (s2b_is_regular_file(
            "/data/data/com.termux/files/usr/etc/tls/cert.pem")) {
        const char *fallback =
            "/data/data/com.termux/files/usr/etc/tls/cert.pem";

        if (setenv("SSL_CERT_FILE", fallback, 1) != 0) {
            return -1;
        }

        return s2b_copy(selected, selected_size, fallback);
    }

    selected[0] = '\0';
    fprintf(
        stderr,
        "stage2b: warning: no usable CA bundle discovered\n"
    );
    return 0;
}

static int
s2b_debug_enabled(void)
{
    const char *value = getenv("CPYTHON_STAGE2_DEBUG");
    return value != NULL &&
           value[0] != '\0' &&
           strcmp(value, "0") != 0;
}

static void
s2b_debug(
    const char *action,
    const struct s2b_paths *paths,
    int ld_was_present,
    const char *ca_file
)
{
    if (!s2b_debug_enabled()) {
        return;
    }

    fprintf(
        stderr,
        "stage2b[r2]: action=%s\n"
        "stage2b[r2]: executable=%s\n"
        "stage2b[r2]: prefix=%s\n"
        "stage2b[r2]: libdir=%s\n"
        "stage2b[r2]: ld_was_present=%d\n"
        "stage2b[r2]: LD_LIBRARY_PATH=%s\n"
        "stage2b[r2]: SSL_CERT_FILE=%s\n",
        action,
        paths->executable,
        paths->prefix,
        paths->libdir,
        ld_was_present,
        getenv("LD_LIBRARY_PATH")
            ? getenv("LD_LIBRARY_PATH")
            : "<unset>",
        ca_file && ca_file[0] ? ca_file : "<unset>"
    );
}

static int
s2b_run_pyconfig(int argc, char **argv)
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

#endif
