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
			--server.port=40002 \
			--server.address=0.0.0.0 \
			./src/app_dash/dashboard/000_Home.py

.PHONY: app_api
app_api:
	poetry run uvicorn src.app_api.main:get_app \
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
docker-compose run --rm app alembic revision --autogenerate -m "Initial"
.PHONY: migrations-check
migrations-check:
	# This will fail if there are any changes to models that are not in migrations.
	@ENV=test poetry run alembic revision --autogenerate --rev-id="rev$(NOWSTAMP)" -m "migration_auto" \
		| grep -q 'No changes in schema detected'

.PHONY: app_celery
app_celery:
	watchmedo auto-restart --directory=./ --pattern=*.py --recursive -- celery -A src.app_celery.main.celery_app worker -c 1 --loglevel=debug

.PHONY: app_celery_flower
app_celery_flower:
	watchmedo auto-restart --directory=./ --pattern=*.py --recursive -- celery -A src.app_celery.main.celery_app flower --port=33901 --loglevel=debug

.PHONY: app_celery_beat
app_celery_beat:
	watchmedo auto-restart --directory=./ --pattern=*.py --recursive -- celery -A src.app_celery.main.celery_app beat --loglevel=debug

.PHONY: compose-up
compose-up:
	docker compose up --build --remove-orphans --wait -d keycloak_db keycloak postgres

.PHONY: compose-down
compose-down:
	docker compose down

.PHONY: cli_scrapper__get_channel_post_youtube
cli_scrapper__get_channel_post_youtube:
	poetry run python -m src.cli_scrapper.main get_channel_posts --source=youtube Hohmemes

.PHONY: cli_scrapper__get_playlist_post_youtube
cli_scrapper__get_playlist_post_youtube:
	poetry run python -m src.cli_scrapper.main get_channel_posts --source=youtube PLVt7fiIBvDPEZV4cxaVT8GCdcpVCfo_a-

.PHONY: cli_scrapper__download_post_youtube
cli_scrapper__download_post_youtube:
	poetry run python -m src.cli_scrapper.main download_post --source=youtube --description Al0fwWuuQWI

.PHONY: cli_scrapper__download_post_youtube2
cli_scrapper__download_post_youtube2:
	poetry run python -m src.cli_scrapper.main download_post --lang=ru --source=youtube --description M_vDEmq3i78 --video_quality low --audio_quality low

.PHONY: cli_scrapper__download_post_youtube2
cli_scrapper__download_post_youtube_error:
	poetry run python -m src.cli_scrapper.main download_post --lang=ru --source=youtube --description M_DEmq3i78 --video_quality low --audio_quality low

.PHONY: cli_scrapper__download_post_youtube3
cli_scrapper__download_post_youtube3:
	poetry run python -m src.cli_scrapper.main download_post --lang=ru --source=youtube --description L-dCUJx1Chg --video_quality medium --audio_quality medium

.PHONY: cli_scrapper__download_post_youtube_mrbeast
cli_scrapper__download_post_youtube_mrbeast:
	poetry run python -m src.cli_scrapper.main download_post --lang=ru --source=youtube --description QbJJwaVdgIs --video_quality medium --audio_quality medium

.PHONY: cli_scrapper__download_post_youtube_strlit
cli_scrapper__download_post_youtube_strlit:
	poetry run python -m src.cli_scrapper.main download_post --lang=ru --source=youtube --description vIQQR_yq-8I --video_quality best --audio_quality best

.PHONY: cli_scrapper__get_channel_post_instagram
cli_scrapper__get_channel_post_instagram:
	poetry run python -m src.cli_scrapper.main get_channel_posts --source=instagram b3r3zko

.PHONY: cli_scrapper__download_post_instagram
cli_scrapper__download_post_instagram_photos:
	poetry run python -m src.cli_scrapper.main download_post --source=instagram --description CvNXNhwowH0 --video_quality low --image_quality low

.PHONY: cli_scrapper__download_post_instagram_videos
	poetry run python -m src.cli_scrapper.main download_post --source=instagram --description C9qIGO0ItH5 --video_quality low

.PHONY: cli_scrapper__download_post_instagram
cli_scrapper__download_post_instagram_video:
	poetry run python -m src.cli_scrapper.main download_post --source=instagram --description C8bsLuvP1PW --video_quality low

.PHONY: cli_scrapper__download_post_instagram
cli_scrapper__download_post_instagram_photo:
	poetry run python -m src.cli_scrapper.main download_post --source=instagram --description CfkIu0xjvtQ --video_quality low

.PHONY: cli_scrapper__get_channel_post_telegram
cli_scrapper__get_channel_post_telegram:
	poetry run python -m src.cli_scrapper.main get_channel_posts --source=telegram mychannelkfing

.PHONY: cli_scrapper__download_post_telegram
cli_scrapper__download_post_telegram:
	poetry run python -m src.cli_scrapper.main download_post --source=telegram --description https://t.me/mychannelkfing/36 --video_quality low

.PHONY: js-compile
js-compile:
	node src/service_paddle/prices_paddle.js
