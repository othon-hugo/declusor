NAME_02       := declusor-02-draftsman
HOST_02       := draftsman
DIR_02        := docker/02-draftsman
DOCKERFILE_02 := $(DIR_02)/draftsman.dockerfile
PORT_SSH_02   := 2202
PORT_API_02   := 8082

.PHONY: build-02 run-02 stop-02 clean-02 ssh-02

build-02:
	@echo "[*] Building image $(NAME_02)..."
	docker build -f $(DOCKERFILE_02) -t $(NAME_02) $(DIR_02)

run-02:
	@echo "[*] Starting $(NAME_02) (SSH: $(PORT_SSH_02), API: $(PORT_API_02))..."
	docker run -d --rm \
		--name $(NAME_02) \
		--hostname $(HOST_02) \
		-p $(PORT_SSH_02):22 \
		-p $(PORT_API_02):8082 \
		$(NAME_02)

stop-02:
	@echo "[*] Stopping $(NAME_02)..."
	@docker stop $(NAME_02) 2>/dev/null || true

clean-02: stop-02
	@echo "[*] Removing container and image $(NAME_02)..."
	@docker rm -f $(NAME_02) 2>/dev/null || true
	@docker rmi -f $(NAME_02) 2>/dev/null || true

ssh-02:
	ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null player@127.0.0.1 -p $(PORT_SSH_02)