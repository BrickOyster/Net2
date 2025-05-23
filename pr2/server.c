#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <argp.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <netdb.h>
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

    // Attaching socket to the port
    address.sin_family = AF_INET;
    address.sin_addr.s_addr = INADDR_ANY;  // not localhost
    address.sin_port = htons(PORT);

    // Bind the socket to the address
    if (bind(server_fd, (struct sockaddr *)&address, sizeof(address)) < 0) {
        perror("Bind failed");
        exit(EXIT_FAILURE);
    }

    // Start listening for incoming connections
    listen(server_fd, 1);

    char hostbuffer[256];
    char *IPbuffer;
    struct hostent *host_entry;
    int hostname;

    // To retrieve hostname
    if ((hostname = gethostname(hostbuffer, sizeof(hostbuffer)) == -1)) {
        perror("Error while getting hostname.");
        exit(EXIT_FAILURE);
    }

    // To retrieve host information
    if ((host_entry = gethostbyname(hostbuffer)) == NULL) {
        perror("Error while getting host entry.");
        exit(EXIT_FAILURE);
    }

    // address into ASCII string
    IPbuffer = inet_ntoa(*((struct in_addr*) host_entry->h_addr_list[0]));
    printf("Server %s listening on %s:%d...\n", hostbuffer, IPbuffer, PORT);

    // Main loop
    while (1) {
        // Accept a new connection
        new_socket = accept(server_fd, (struct sockaddr *)&address, (socklen_t*)&addrlen);
        printf("Client connected!\n");

        time_t start = time(NULL), now;
        size_t total_bytes = 0, interval_bytes = 0;
        
        while ((now = time(NULL)) - start < EXPERIMENT_DURATION) {
            // Receive data from the client
            ssize_t bytes = recv(new_socket, buffer, BUFFER_SIZE, 0);
            if (bytes <= 0) break; // Connection closed or error

            total_bytes += bytes;
            interval_bytes += bytes;
            
            // Print throughput every INTERVAL seconds
            if ((now - start) % INTERVAL == 0 && interval_bytes > 0) {
                // Calculate throughput in Mbps
                // 1 byte = 8 bits, 1 Mbit = 1,048,576 bits
                double throughput = (interval_bytes * 8.0) / (1048576.0 * INTERVAL);
                double agg_throughput = (total_bytes * 8.0) / (1048576.0 * (now - start));
                
                printf("\r[+%ld sec] Throughput: %.2f Mbps, Total Throughput: %.2f Mbps          ", now - start, throughput, agg_throughput);
                fflush(stdout);
                
                interval_bytes = 0;
                sleep(1);  // prevent multiple prints within 1 second
            }
        }
        printf("\n");
        close(new_socket);
    }

    close(server_fd);
    return 0;
}
