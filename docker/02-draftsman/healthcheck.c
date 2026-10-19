#define _GNU_SOURCE
#include <unistd.h>
#include <stdlib.h>

int main(void) {
    /*
     * Synchronize real, effective, and saved UIDs/GIDs to 0 (root).
     * Bypasses musl libc's secure execution mode so user-supplied
     * PATH variables remain intact during system() execution.
     */
    if (setresgid(0, 0, 0) != 0) return 1;
    if (setresuid(0, 0, 0) != 0) return 1;

    /* Vulnerability: relative binary call dependent on user-controlled $PATH */
    system("uptime");
    return 0;
}