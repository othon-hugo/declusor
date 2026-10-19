.PHONY: all build-labs run-labs stop-labs clean-labs status-labs help-labs help

all: help

include docker/01-skiff/skiff.mk
include docker/02-draftsman/draftsman.mk
include docker/03-dockside/dockside.mk
include docker/04-leviathan/leviathan.mk

build-labs: build-01 build-02 build-03 build-04

run-labs: run-01 run-02 run-03 run-04

stop-labs: stop-01 stop-02 stop-03 stop-04

clean-labs: clean-01 clean-02 clean-03 clean-04
	@echo "[+] Declusor environment completely wiped."

status-labs:
	@docker ps -a --filter "name=declusor-" --format "table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}"

help-labs:
	@echo "======================================================================"
	@echo " Declusor Labs - Management Commands"
	@echo "======================================================================"
	@echo " Global targets:"
	@echo "   make build-labs      Build all 4 challenge Docker images"
	@echo "   make run-labs        Start all 4 containers in background"
	@echo "   make stop-labs       Stop all running containers"
	@echo "   make clean-labs      Stop and remove all containers and built images"
	@echo "   make status-labs     Display running state and ports of all containers"
	@echo ""
	@echo " Individual targets (replace XX with 01, 02, 03, or 04):"
	@echo "   make build-XX        Build image for lab XX only"
	@echo "   make run-XX          Start container for lab XX only"
	@echo "   make stop-XX         Stop container for lab XX only"
	@echo "   make clean-XX        Remove container and image for lab XX only"
	@echo "   make ssh-XX          Connect directly via SSH as 'player' to lab XX"
	@echo "======================================================================"

help: help-labs
