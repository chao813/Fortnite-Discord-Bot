IMAGE_NAME = discord_bots/fortnite:latest
CONTAINER_NAME = fornite_discord_bot
PORT = 5100

TEST_PLAYER_NAME = kwklin

.PHONY: build run run-detached run-interactive test stop logs

build:
	docker build -t $(IMAGE_NAME) .

run:
	docker run --rm --name $(CONTAINER_NAME) -p $(PORT):5000 $(IMAGE_NAME)

run-detached:
	docker run -d --name $(CONTAINER_NAME) -p $(PORT):5000 $(IMAGE_NAME)

run-interactive:
	docker run --rm -it -v $(shell pwd):/app $(IMAGE_NAME) /bin/sh

test:
	docker run --rm -v $(shell pwd):/app $(IMAGE_NAME) \
		python3 -m scripts.test_player_stats $(TEST_PLAYER_NAME)

stop:
	docker stop $(CONTAINER_NAME) || true
	docker rm $(CONTAINER_NAME) || true

logs:
	docker logs -f $(CONTAINER_NAME)
