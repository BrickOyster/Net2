#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <argp.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <time.h>

int PORT = 5001;
int BUFFER_SIZE = 8192;
int EXPERIMENT_DURATION = 31;
int INTERVAL = 2;

int main(int argc, char const* argv[]) {
    int server_fd, new_socket;
    struct sockaddr_in address;
    int addrlen = sizeof(address);
    char buffer[BUFFER_SIZE];
    
    // Parse command line options
    int argopt;
    while ((argopt = getopt(argc, (char * const *)argv, "p:b:d:i:")) != -1) {
        switch (argopt) {
            case 'p':
                PORT = atoi(optarg);
                break;
            case 'b':
                BUFFER_SIZE = atoi(optarg);
                break;
            case 'd':
                EXPERIMENT_DURATION = atoi(optarg);
                break;
            case 'i':
                INTERVAL = atoi(optarg);
                break;
            default:
                fprintf(stderr, "Usage: %s [-p port] [-b buffer_size] [-d duration] [-i interval]\n", argv[0]);
                exit(EXIT_FAILURE);
        }
    }

    // Create socket file descriptor
    server_fd = socket(AF_INET, SOCK_STREAM, 0);
    if (server_fd == 0) {
        perror("Socket failed");
        exit(EXIT_FAILURE);
    }

    int opt = 1;
    setsockopt(server_fd, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt));

    return 0;
}
