# ================================================================================================ #

include docker/01-skiff/skiff.mk
include docker/02-draftsman/draftsman.mk
include docker/03-dockside/dockside.mk
include docker/04-leviathan/leviathan.mk

.PHONY: all build-all run-all stop-all clean status help

all: build-all

build-all: build-01 build-02 build-03 build-04

run-all: run-01 run-02 run-03 run-04

stop-all: stop-01 stop-02 stop-03 stop-04

clean: clean-01 clean-02 clean-03 clean-04
	@echo "[+] Declusor environment completely wiped."

status:
	@docker ps -a --filter "name=declusor-" --format "table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}"

help:
	@echo "======================================================================"
	@echo " Declusor CTF - Management Commands"
	@echo "======================================================================"
	@echo " Global targets:"
	@echo "   make build-all       Build all 4 challenge Docker images"
	@echo "   make run-all         Start all 4 containers in background"
	@echo "   make stop-all        Stop all running containers"
	@echo "   make clean           Stop and remove all containers and built images"
	@echo "   make status          Display running state and ports of all containers"
	@echo ""
	@echo " Individual targets (replace XX with 01, 02, 03, or 04):"
	@echo "   make build-XX        Build image for lab XX only"
	@echo "   make run-XX          Start container for lab XX only"
	@echo "   make stop-XX         Stop container for lab XX only"
	@echo "   make clean-XX        Remove container and image for lab XX only"
	@echo "   make ssh-XX          Connect directly via SSH as 'player' to lab XX"
	@echo "======================================================================"
