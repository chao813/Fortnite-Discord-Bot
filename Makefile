.PHONY: build run run-dev run-interactive stop logs test

build:
	docker compose build

run:
	docker compose -f docker-compose.yaml -f docker-compose.prod.yaml up -d

run-dev:
	docker compose up

run-interactive:
	docker compose run --rm --entrypoint /bin/sh app

test:
	docker compose run --rm app python3 -m scripts.test_player_stats

stop:
	docker compose down

logs:
	docker compose logs -f
