#include <Python.h>
#include <errno.h>
#include <pthread.h>
#include <signal.h>
#include <stdio.h>

static int init_android_signals(void) {
    sigset_t set;
    int rc;
    if (sigemptyset(&set) != 0) return errno ? errno : 1;
    if (sigaddset(&set, SIGUSR1) != 0) return errno ? errno : 1;
    rc = pthread_sigmask(SIG_UNBLOCK, &set, NULL);
    return rc;
}

int main(int argc, char **argv) {
    int rc = init_android_signals();
    if (rc != 0) {
        fprintf(stderr, "launcher-la3: pthread_sigmask(SIGUSR1): %d\n", rc);
        return 70;
    }
    return Py_BytesMain(argc, argv);
}
