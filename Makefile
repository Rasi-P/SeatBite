.PHONY: up down seed test build migrate

up:
	docker compose up --build

down:
	docker compose down

migrate:
	docker compose run --rm backend python manage.py migrate

seed:
	docker compose run --rm backend python manage.py seed_demo

test:
	docker compose run --rm backend python manage.py test

build:
	docker compose run --rm frontend npm run build

