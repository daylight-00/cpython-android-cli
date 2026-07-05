/*
 * Stage 2 / S2-R
 *
 * Self-locate the prefix. On the first pass:
 *   - configure LD_LIBRARY_PATH in the environment,
 *   - configure SSL_CERT_FILE,
 *   - re-exec /proc/self/exe with the original argv.
 *
 * On the second pass:
 *   - remove the private recursion guard from the environment,
 *   - run the Stage 1-B B0 PyConfig frontend.
 *
 * The original argv vector is preserved across execv().
 */

#include "stage2-common.h"

int
main(int argc, char **argv)
{
    const char *guard;
    struct s2_paths paths;
    char combined[PATH_MAX * 2];

    if (s2_discover_paths(&paths) != 0) {
        return 70;
    }

    guard = getenv("_CPYTHON_STAGE2_REEXEC");

    if (guard == NULL || strcmp(guard, "1") != 0) {
        if (s2_configure_ld_env(
                &paths, combined, sizeof(combined)) != 0) {
            return 71;
        }

        if (s2_configure_ca() != 0) {
            return 72;
        }

        if (setenv("_CPYTHON_STAGE2_REEXEC", "1", 1) != 0) {
            fprintf(stderr,
                    "stage2: set reexec guard: %s\n",
                    strerror(errno));
            return 73;
        }

        s2_print_diagnostics("reexec-first-pass", &paths);

        execv(paths.executable, argv);

        fprintf(stderr,
                "stage2: execv(%s): %s\n",
                paths.executable,
                strerror(errno));
        return 74;
    }

    /*
     * Do not leak the recursion guard into Python subprocesses. Children
     * launched through sys.executable should perform their own bootstrap.
     */
    unsetenv("_CPYTHON_STAGE2_REEXEC");

    s2_print_diagnostics("reexec-second-pass", &paths);
    return s2_run_pyconfig(argc, argv);
}
