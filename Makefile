include .env
export

dev: export DEV_RUN=true
dev:
	python main.py

clean:
	rm -rf ./courses
