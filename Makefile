SHELL:=bash
NOWSTAMP := $(shell bash -c 'date -u +"%Y%m%dT%H%M%S"')
CWD := $(shell bash -c 'pwd')

.PHONY: setup
setup:
	poetry install --sync
	make compose-up
	make migrations-run
	#git config core.hooksPath dev/.githooks

.PHONY: dev
dev:
	make format
	make lint
	make compose-up
	make test

safety:
	#poetry run safety check --full-report
	poetry run pip check
	poetry check

.PHONY: lint
lint:
	poetry run ruff check --respect-gitignore --fix --extend-exclude tests ./
	poetry run ruff format --diff --respect-gitignore
	poetry run mypy --exclude migration/ .
	poetry run pyright src/

.PHONY: format
format:
	poetry run ruff format --respect-gitignore --preview .

.PHONY: test
test:
	ENV=test poetry run pytest -vv --exitfirst --failed-first --log-level debug

.PHONY: test_mocked
test_mocked:
	TEST_MOCK_CACHE=1 ENV=test poetry run pytest -vv --exitfirst --failed-first

.PHONY: test_no_logs
test_no_logs:
	TEST_NO_TRACEBACK=1 ENV=test poetry run pytest -vv --capture=no --exitfirst --failed-first

.PHONY: test_failed
test_failed:
	make test-failed

.PHONY: test-failed
test-failed:
	ENV=test PYTHONPATH=${CWD} poetry run pytest -vv --full-trace --failed-first --exitfirst --last-failed --show-capture=all

.PHONY: test-specific
test-specific:
	# add your test here
	ENV=test PYTHONPATH=${CWD} poetry run pytest -vv --full-trace --failed-first --exitfirst --show-capture=all ./tests/tests/checkout/test_paddle_webhook.py

.PHONY: test-cov
test-cov:
	ENV=test PYTHONPATH=${CWD} poetry run pytest \
		--cov=src \
		--cov=external \
		--cov-report=xml \
		--cov-report=html \
		--cov-report=term-missing:skip-covered \
		--cov-fail-under=70.0

.PHONY: app_dash
app_dash:
	watchmedo auto-restart --directory=./ --pattern=*.py --recursive -- \
		poetry run python -m streamlit run \
			--server.fileWatcherType=none \
			--server.headless=true \
			--client.toolbarMode=developer \
			--server.port=40008 \
			--server.address=0.0.0.0 \
			./src/app_dash/dashboard/000_Home.py

.PHONY: app_api
app_api:
	poetry run uvicorn src.parsing_app_api.main:get_app \
		--timeout-graceful-shutdown 10 \
		--limit-max-requests 1024 \
		--loop asyncio \
		--use-colors \
		--reload \
		--host 0.0.0.0 \
		--port 40001 \
		--log-level error \
		--no-access-log

.PHONY: migrations-run
migrations-run:
	ENV=test poetry run alembic upgrade head

.PHONY: migrations-add
migrations-add:
	@ENV=test poetry run alembic revision --rev-id="rev$(NOWSTAMP)" -m "migration_manual"

.PHONY: migrations-check
migrations-check:
	# This will fail if there are any changes to models that are not in migrations.
	@ENV=test poetry run alembic revision --autogenerate --rev-id="rev$(NOWSTAMP)" -m "migration_auto" \
		| grep -q 'No changes in schema detected'

.PHONY: app_celery
app_celery:
	watchmedo auto-restart --directory=./ --pattern=*.py --recursive -- celery -A src.app_celery.main.app worker -c 1 --loglevel=debug

.PHONY: app_celery_flower
app_celery_flower:
	watchmedo auto-restart --directory=./ --pattern=*.py --recursive -- celery -A src.app_celery.main.celery_app flower --port=33901 --loglevel=debug

.PHONY: app_celery_beat
app_celery_beat:
	watchmedo auto-restart --directory=./ --pattern=*.py --recursive -- celery -A src.app_celery.main.app beat --loglevel=debug

.PHONY: compose-up
compose-up:
	docker compose up --build --remove-orphans --wait -d keycloak_db keycloak postgres

.PHONY: compose-down
compose-down:
	docker compose down

.PHONY: js-compile
js-compile:
	node src/service_paddle/prices_paddle.js
