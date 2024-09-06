
format:
	isort .
	autoflake --in-place --remove-all-unused-imports .
	black .