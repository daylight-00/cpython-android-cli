/*
 * CPython Android CLI launcher — Stage 2-C synthesis candidate.
 *
 * Runtime policy:
 *
 *   1. Resolve the actual executable with /proc/self/exe.
 *   2. Derive:
 *
 *        <prefix>/bin/python3.14
 *                  -> <prefix>
 *                  -> <prefix>/lib
 *
 *   3. Ensure <prefix>/lib appears exactly once in LD_LIBRARY_PATH.
 *   4. If it was absent when this process started:
 *        - repair the environment,
 *        - configure a usable CA bundle,
 *        - execv() the actual executable with the original argv.
 *   5. Otherwise:
 *        - repair/discover SSL_CERT_FILE if necessary,
 *        - enter the frozen Stage 1-B B0 PyConfig frontend.
 *
 * The condition is the re-exec fixed point. No private recursion guard is
 * required. Child processes launched through sys.executable inherit a ready
 * loader environment and normally enter Python directly.
 */

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

struct runtime_paths {
    char executable[PATH_MAX];
    char prefix[PATH_MAX];
    char libdir[PATH_MAX];
};

static int
is_regular_file(const char *path)
{
    struct stat st;

    return path != NULL &&
           path[0] != '\0' &&
           stat(path, &st) == 0 &&
           S_ISREG(st.st_mode);
}

static int
copy_string(char *dst, size_t dst_size, const char *src)
{
    int n = snprintf(dst, dst_size, "%s", src);
    return n >= 0 && (size_t)n < dst_size ? 0 : -1;
}

static int
parent_dir(char *path)
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
discover_runtime_paths(struct runtime_paths *paths)
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
            "python-stage2c: readlink(/proc/self/exe): %s\n",
            strerror(errno)
        );
        return -1;
    }

    paths->executable[n] = '\0';

    if (copy_string(
            paths->prefix,
            sizeof(paths->prefix),
            paths->executable) != 0) {
        fprintf(stderr, "python-stage2c: executable path too long\n");
        return -1;
    }

    /* <prefix>/bin/<launcher> -> <prefix> */
    if (parent_dir(paths->prefix) != 0 ||
        parent_dir(paths->prefix) != 0) {
        fprintf(
            stderr,
            "python-stage2c: cannot derive prefix from %s\n",
            paths->executable
        );
        return -1;
    }

    if (snprintf(
            paths->libdir,
            sizeof(paths->libdir),
            "%s/lib",
            paths->prefix) >= (int)sizeof(paths->libdir)) {
        fprintf(stderr, "python-stage2c: libdir path too long\n");
        return -1;
    }

    return 0;
}

static int
component_equals(
    const char *start,
    size_t length,
    const char *wanted
)
{
    size_t wanted_len = strlen(wanted);

    return length == wanted_len &&
           memcmp(start, wanted, length) == 0;
}

/*
 * Ensure WANTED occurs exactly once in LIST.
 *
 * If absent, prepend it.
 * If duplicated, keep the first occurrence and remove later copies.
 * Preserve the order of all other components.
 */
static int
normalize_required_path(
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
    int first_output = 1;

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
        if (!first_output) {                                              \
            APPEND_BYTES(":", 1);                                         \
        }                                                                 \
        first_output = 0;                                                 \
    } while (0)

    if (list == NULL || list[0] == '\0') {
        if (snprintf(out, out_size, "%s", wanted) >= (int)out_size) {
            return -1;
        }

        *was_present = 0;
        return 0;
    }

    out[0] = '\0';
    start = list;

    for (p = list; ; p++) {
        if (*p == ':' || *p == '\0') {
            size_t len = (size_t)(p - start);
            int is_wanted = component_equals(start, len, wanted);

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

        if (copy_string(preserved, sizeof(preserved), out) != 0) {
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
configure_ca_bundle(void)
{
    char candidate[PATH_MAX];
    const char *existing = getenv("SSL_CERT_FILE");
    const char *termux_prefix = getenv("PREFIX");

    if (is_regular_file(existing)) {
        return 0;
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
            is_regular_file(candidate)) {
            return setenv("SSL_CERT_FILE", candidate, 1);
        }
    }

    if (is_regular_file(
            "/data/data/com.termux/files/usr/etc/tls/cert.pem")) {
        return setenv(
            "SSL_CERT_FILE",
            "/data/data/com.termux/files/usr/etc/tls/cert.pem",
            1
        );
    }

    fprintf(
        stderr,
        "python-stage2c: warning: no usable CA bundle discovered\n"
    );

    return 0;
}

static int
run_python(int argc, char **argv)
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

int
main(int argc, char **argv)
{
    struct runtime_paths paths;
    char normalized_ld[PATH_MAX * 4];
    const char *current_ld;
    int libdir_was_present = 0;

    if (discover_runtime_paths(&paths) != 0) {
        return 70;
    }

    current_ld = getenv("LD_LIBRARY_PATH");

    if (normalize_required_path(
            current_ld,
            paths.libdir,
            normalized_ld,
            sizeof(normalized_ld),
            &libdir_was_present) != 0) {
        fprintf(
            stderr,
            "python-stage2c: failed to normalize LD_LIBRARY_PATH\n"
        );
        return 71;
    }

    if (setenv("LD_LIBRARY_PATH", normalized_ld, 1) != 0) {
        fprintf(
            stderr,
            "python-stage2c: setenv(LD_LIBRARY_PATH): %s\n",
            strerror(errno)
        );
        return 72;
    }

    if (configure_ca_bundle() != 0) {
        fprintf(
            stderr,
            "python-stage2c: failed to configure SSL_CERT_FILE\n"
        );
        return 73;
    }

    if (!libdir_was_present) {
        execv(paths.executable, argv);

        fprintf(
            stderr,
            "python-stage2c: execv(%s): %s\n",
            paths.executable,
            strerror(errno)
        );
        return 74;
    }

    return run_python(argc, argv);
}
