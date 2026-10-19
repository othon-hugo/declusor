NAME_01       := declusor-01-skiff
HOST_01       := skiff
DIR_01        := docker/01-skiff
DOCKERFILE_01 := $(DIR_01)/skiff.dockerfile
PORT_01       := 2201

.PHONY: build-01 run-01 stop-01 clean-01 ssh-01

build-01:
	@echo "[*] Building image $(NAME_01)..."
	docker build -f $(DOCKERFILE_01) -t $(NAME_01) $(DIR_01)

run-01:
	@echo "[*] Starting container $(NAME_01) on port $(PORT_01)..."
	docker run -d --rm \
		--name $(NAME_01) \
		--hostname $(HOST_01) \
		-p $(PORT_01):22 \
		$(NAME_01)

stop-01:
	@echo "[*] Stopping $(NAME_01)..."
	@docker stop $(NAME_01) 2>/dev/null || true

clean-01: stop-01
	@echo "[*] Removing container and image $(NAME_01)..."
	@docker rm -f $(NAME_01) 2>/dev/null || true
	@docker rmi -f $(NAME_01) 2>/dev/null || true

ssh-01:
	ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null player@127.0.0.1 -p $(PORT_01)