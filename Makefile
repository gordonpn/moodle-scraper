.DEFAULT_GOAL := help
.PHONY: dev clean format help run
BIN=venv/bin/
include .env
export

help: ## show this help
	@egrep -h '\s##\s' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[33m%-20s\033[0m %s\n", $$1, $$2}'

dev: export DEV_RUN=true
dev: ## run script locally
	$(BIN)python main.py

clean: ## remove downloaded files
	rm -rf ./courses
	find . -name "*.pyc" -exec rm -rf {} \;

format: ## format with black
	$(BIN)black -t py38 ./

run: ## build and run docker image
	docker build -t moodle-scraper . && docker run -it --rm -e DEV_RUN=true --env-file .env moodle-scraper
