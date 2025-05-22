CC = gcc
CFLAGS = -Wall -O2
TARGETS = client server sniffer

all: $(TARGETS)

client: client.c
	$(CC) $(CFLAGS) -o client client.c

server: server.c
	$(CC) $(CFLAGS) -o server server.c

sniffer: sniffer.c
	$(CC) $(CFLAGS) -o sniffer sniffer.c

clean:
	rm -f $(TARGETS)