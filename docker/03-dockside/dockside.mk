NAME_03       := declusor-03-dockside
HOST_03       := dockside
DIR_03        := docker/03-dockside
DOCKERFILE_03 := $(DIR_03)/dockside.dockerfile
PORT_SSH_03   := 2203

.PHONY: build-03 run-03 stop-03 clean-03 ssh-03

build-03:
	@echo "[*] Building image $(NAME_03)..."
	docker build -f $(DOCKERFILE_03) -t $(NAME_03) $(DIR_03)

run-03:
	@echo "[*] Starting $(NAME_03) (SSH: $(PORT_SSH_03))..."
	docker run -d --rm \
		--name $(NAME_03) \
		--hostname $(HOST_03) \
		-p $(PORT_SSH_03):22 \
		-v /var/run/docker.sock:/var/run/docker.sock \
		$(NAME_03)

stop-03:
	@echo "[*] Stopping $(NAME_03)..."
	@docker stop $(NAME_03) 2>/dev/null || true

clean-03: stop-03
	@echo "[*] Removing container and image $(NAME_03)..."
	@docker rm -f $(NAME_03) 2>/dev/null || true
	@docker rmi -f $(NAME_03) 2>/dev/null || true

ssh-03:
	ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null player@127.0.0.1 -p $(PORT_SSH_03)