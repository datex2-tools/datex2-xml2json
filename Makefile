.PHONY: lint-fix
lint-fix:
	ruff format ./datex2_xml2json ./tests
	ruff check --fix ./datex2_xml2json ./tests
	# mypy has no fix mode, we run it anyway to report (unfixable) errors
	mypy ./datex2_xml2json ./tests

.PHONY: lint-check
lint-check:
	ruff format --check --diff ./datex2_xml2json ./tests
	ruff check ./datex2_xml2json ./tests
	mypy ./datex2_xml2json ./tests