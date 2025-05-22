#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <argp.h>
#include <arpa/inet.h>
#include <time.h>

char *SERVER_IP = "0.0.0.0";  // Change to actual server IP
int PORT = 5001;
int BUFFER_SIZE = 8192;
int INTERVAL = 2;

int main(int argc, char const* argv[]) {
    // Parse command line options
    int argopt;
    while ((argopt = getopt(argc, (char * const *)argv, "a:p:b:i:")) != -1) {
        switch (argopt) {
            case 'a':
                SERVER_IP = optarg;
                break;
            case 'p':
                PORT = atoi(optarg);
                break;
            case 'b':
                BUFFER_SIZE = atoi(optarg);
                break;
            case 'i':
                INTERVAL = atoi(optarg);
                break;
            default:
                fprintf(stderr, "Usage: %s [-p port] [-b buffer_size] [-d duration] [-i interval]\n", argv[0]);
                exit(EXIT_FAILURE);
        }
    }

    return 0;
}