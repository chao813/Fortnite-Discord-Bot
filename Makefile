IMAGE_NAME = discord_bots/fortnite:latest
CONTAINER_NAME = fornite_discord_bot
PORT = 5100

ENV_VAR_ARGS = --env-file .env
VOL_MOUNT_ARGS = -v $(shell pwd):/app

TEST_PLAYER_NAME = kwklin

.PHONY: build run run-dev run-interactive test stop logs

build:
	docker build -t $(IMAGE_NAME) .

run:
	docker run -d --name $(CONTAINER_NAME) -p $(PORT):$(PORT) $(ENV_VAR_ARGS) $(IMAGE_NAME)

run-dev:
	docker run --rm --name $(CONTAINER_NAME) -p $(PORT):$(PORT) $(VOL_MOUNT_ARGS) $(ENV_VAR_ARGS) $(IMAGE_NAME)
	make logs

run-interactive:
	docker run --rm -it $(VOL_MOUNT_ARGS) $(ENV_VAR_ARGS) $(IMAGE_NAME) /bin/sh

test:
	docker run --rm $(VOL_MOUNT_ARGS) $(ENV_VAR_ARGS) $(IMAGE_NAME) \
		python3 -m scripts.test_player_stats $(TEST_PLAYER_NAME)

stop:
	docker stop $(CONTAINER_NAME) || true
	docker rm $(CONTAINER_NAME) || true

logs:
	docker logs -f $(CONTAINER_NAME)
