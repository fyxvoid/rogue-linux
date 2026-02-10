#include <stdio.h>
#include <unistd.h>

int main() {
    printf("Hello from inside the isolated rootfs!\n");
    printf("PID: %d\n", getpid());
    printf("CWD: %s\n", getcwd(NULL, 0));
    return 0;
}
