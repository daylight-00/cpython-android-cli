/*
 * Stage 2 / S2-E
 *
 * Self-locate the prefix, then call setenv() for:
 *   LD_LIBRARY_PATH
 *   SSL_CERT_FILE
 *
 * This intentionally does NOT call the bionic linker update API and does
 * NOT re-exec. It is an experimental control for measuring whether changing
 * the environment alone is sufficient for later extension-module dlopen.
 */

#include "stage2-common.h"

int
main(int argc, char **argv)
{
    struct s2_paths paths;
    char combined[PATH_MAX * 2];

    if (s2_discover_paths(&paths) != 0) {
        return 70;
    }

    if (s2_configure_ld_env(&paths, combined, sizeof(combined)) != 0) {
        return 71;
    }

    if (s2_configure_ca() != 0) {
        return 72;
    }

    s2_print_diagnostics("setenv", &paths);
    return s2_run_pyconfig(argc, argv);
}
