/*
 * Stage 2-B / R2 conditional self re-exec.
 *
 * Policy:
 *
 * 1. Resolve the actual executable through /proc/self/exe.
 * 2. Derive <prefix> and <prefix>/lib.
 * 3. Inspect the inherited LD_LIBRARY_PATH.
 * 4. Ensure <prefix>/lib occurs exactly once in the environment value.
 * 5. If <prefix>/lib was absent at process start:
 *      - update the environment,
 *      - configure a usable CA bundle,
 *      - execv() the actual executable with the original argv.
 * 6. If <prefix>/lib was already present:
 *      - do not re-exec,
 *      - repair/discover SSL_CERT_FILE if necessary,
 *      - enter the Stage 1-B B0 PyConfig frontend.
 *
 * There is no recursion guard. The condition itself is the fixed point:
 * after the first exec, the required library directory is present.
 */

#include "stage2b-common.h"

int
main(int argc, char **argv)
{
    struct s2b_paths paths;
    char normalized_ld[PATH_MAX * 4];
    char selected_ca[PATH_MAX];
    const char *current_ld;
    int ld_was_present = 0;

    if (s2b_discover_paths(&paths) != 0) {
        return 70;
    }

    current_ld = getenv("LD_LIBRARY_PATH");

    if (s2b_normalize_required_path(
            current_ld,
            paths.libdir,
            normalized_ld,
            sizeof(normalized_ld),
            &ld_was_present) != 0) {
        fprintf(
            stderr,
            "stage2b: failed to normalize LD_LIBRARY_PATH\n"
        );
        return 71;
    }

    if (setenv("LD_LIBRARY_PATH", normalized_ld, 1) != 0) {
        fprintf(
            stderr,
            "stage2b: setenv(LD_LIBRARY_PATH): %s\n",
            strerror(errno)
        );
        return 72;
    }

    if (s2b_configure_ca(
            selected_ca,
            sizeof(selected_ca)) != 0) {
        fprintf(
            stderr,
            "stage2b: failed to configure SSL_CERT_FILE\n"
        );
        return 73;
    }

    if (!ld_was_present) {
        s2b_debug(
            "reexec",
            &paths,
            ld_was_present,
            selected_ca
        );

        execv(paths.executable, argv);

        fprintf(
            stderr,
            "stage2b: execv(%s): %s\n",
            paths.executable,
            strerror(errno)
        );
        return 74;
    }

    s2b_debug(
        "direct",
        &paths,
        ld_was_present,
        selected_ca
    );

    return s2b_run_pyconfig(argc, argv);
}
