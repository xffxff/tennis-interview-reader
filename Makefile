
format:
	isort .
	autoflake --in-place --remove-all-unused-imports --exclude="__init__.py" .
	black .