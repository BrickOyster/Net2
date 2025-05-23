CC = gcc
CFLAGS = -Wall -O2
TARGETS = client server

all: $(TARGETS)

client: client.c
	$(CC) $(CFLAGS) -o client client.c

server: server.c
	$(CC) $(CFLAGS) -o server server.c

clean:
	rm -f $(TARGETS)