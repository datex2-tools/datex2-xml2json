MAIN_MODULE=./src/datex2_xml2json
OTHER_MODULES=./tests

.PHONY: lint-fix
lint-fix:
	uv run ruff format ${MAIN_MODULE} ${OTHER_MODULES}
	uv run ruff check --fix ${MAIN_MODULE} ${OTHER_MODULES}
	# mypy has no fix mode, we run it anyway to report (unfixable) errors
	uv run mypy ${MAIN_MODULE} ${OTHER_MODULES}

.PHONY: lint-check
lint-check:
	uv run ruff format --check --diff ${MAIN_MODULE} ${OTHER_MODULES}
	uv run ruff check ${MAIN_MODULE} ${OTHER_MODULES}
	uv run mypy ${MAIN_MODULE} ${OTHER_MODULES}