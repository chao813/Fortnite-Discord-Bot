.PHONY: install start start-dev cp-test build-dist clean clean-all

install:
	npm install

start:
	npm start

start-dev:
	rm -f src/replay-files/test_1.replay && npm start

cp-test:
	cp src/replay-files/ranked_br_duo_1.replay src/replay-files/test_1.replay

build-win:
	env | grep -iE 'DEBUG|NODE_|ELECTRON_|NPM_|GH_|GITHUB_' > envfile || true
	docker run --rm -ti \
		--env-file envfile \
		--env ELECTRON_CACHE="/root/.cache/electron" \
		--env ELECTRON_BUILDER_CACHE="/root/.cache/electron-builder" \
		-v ${PWD}:/project \
		-v fortnite-node-modules:/project/node_modules \
		-v ~/.cache/electron:/root/.cache/electron \
		-v ~/.cache/electron-builder:/root/.cache/electron-builder \
		electronuserland/builder:wine \
		/bin/bash -c "npm install && npm run dist:win"
	rm -f envfile

build-mac:
	npm run dist:mac

clean:
	rm -rf dist/
	@echo "Cleaned build artifacts"

clean-all: clean
	docker volume rm fortnite-node-modules || true
	@echo "Removed node_modules volume"
