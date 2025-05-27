#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <argp.h>
#include <arpa/inet.h>
#include <time.h>

char *SERVER_IP = "0.0.0.0"; // Default to localhost
int PORT = 5001;
int BUFFER_SIZE = 128 * 1024; // 128 KB default buffer size
int DURATION = 30;
int INTERVAL = 2;

int main(int argc, char const* argv[]) {
    int sock = 0;
    struct sockaddr_in serv_addr;
    char buffer[BUFFER_SIZE];
    memset(buffer, 'A', sizeof(buffer));
    
    // Parse command line options
    int argopt;
    while ((argopt = getopt(argc, (char * const *)argv, "a:p:b:i:d:hH?")) != -1) {
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
            case 'd':
                DURATION = atoi(optarg);
                break;
            case 'h' || 'H' || '?':
                printf("Usage: %s [-a ip] [-p port] [-b buffer_size] [-i interval [-d duration] [-h]/[-H]/[-?]]\n", argv[0]);
                exit(EXIT_SUCCESS);
            default:
                fprintf(stderr, "Usage: %s [-a ip] [-p port] [-b buffer_size] [-i interval] [-d duration] [-h]/[-H]/[-?]\n", argv[0]);
                exit(EXIT_FAILURE);
        }
    }

    // Create socket
    if ((sock = socket(AF_INET, SOCK_STREAM, 0)) < 0) {
        perror("Socket creation error");
        return -1;
    }

    // Set socket options
    serv_addr.sin_family = AF_INET;
    serv_addr.sin_port = htons(PORT);

    // Check if the server IP is valid
    if (inet_pton(AF_INET, SERVER_IP, &serv_addr.sin_addr) <= 0) {
        perror("Invalid address/ Address not supported");
        return -1;
    }

    // Connect to the server
    if (connect(sock, (struct sockaddr *)&serv_addr, sizeof(serv_addr)) < 0) {
        perror("Connection Failed");
        return -1;
    }
    printf("Connected to server. Starting SpeedTest...\n");

    time_t start = time(NULL), last_print = start, now;
    size_t interval_bytes = 0, total_bytes = 0;

    // Main loop to send data
    while ((now = time(NULL)) - start < DURATION + INTERVAL/10) {
        ssize_t bytes = send(sock, buffer, BUFFER_SIZE, 0);
        if (bytes <= 0) break;

        interval_bytes += bytes;
        total_bytes += bytes;

        // Print sent data every INTERVAL seconds
        if ((now - last_print) >= INTERVAL && interval_bytes > 0) {
            printf("\r[+%ld sec] Sent: %.2f Mbits (%.2f Mbits in %d seconds)          ", now - start, (total_bytes * 8.0) / 1048576.0, (interval_bytes * 8.0) / 1048576.0, INTERVAL);
            fflush(stdout);
            interval_bytes = 0;
            last_print = now;
        }
    }

    printf("\n");
    close(sock);
    return 0;
}