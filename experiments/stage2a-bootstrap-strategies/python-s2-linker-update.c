/*
 * Stage 2 / S2-U
 *
 * Self-locate the prefix, update the Android bionic linker search path
 * in-process, configure the Termux CA bundle, then run the Stage 1-B B0
 * PyConfig frontend.
 *
 * android_update_LD_LIBRARY_PATH is resolved dynamically so this remains
 * an experiment with an explicitly measured availability boundary.
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

    if (s2_update_bionic_linker(
            &paths, combined, sizeof(combined)) != 0) {
        return 71;
    }

    if (s2_configure_ca() != 0) {
        return 72;
    }

    s2_print_diagnostics("linker-update", &paths);
    return s2_run_pyconfig(argc, argv);
}
