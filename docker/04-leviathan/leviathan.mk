NAME_04       := declusor-04-leviathan
HOST_04       := leviathan
DIR_04        := docker/04-leviathan
DOCKERFILE_04 := $(DIR_04)/leviathan.dockerfile
PORT_04       := 2204

.PHONY: build-04 run-04 stop-04 clean-04 ssh-04

build-04:
	@echo "[*] Building image $(NAME_04)..."
	docker build -f $(DOCKERFILE_04) -t $(NAME_04) $(DIR_04)

run-04:
	@echo "[*] Starting container $(NAME_04) (privileged mode) on port $(PORT_04)..."
	docker run -d --rm \
		--name $(NAME_04) \
		--hostname $(HOST_04) \
		--privileged \
		-p $(PORT_04):22 \
		$(NAME_04)

stop-04:
	@echo "[*] Stopping $(NAME_04)..."
	@docker stop $(NAME_04) 2>/dev/null || true

clean-04: stop-04
	@echo "[*] Removing container and image $(NAME_04)..."
	@docker rm -f $(NAME_04) 2>/dev/null || true
	@docker rmi -f $(NAME_04) 2>/dev/null || true

ssh-04:
	ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null player@127.0.0.1 -p $(PORT_04)