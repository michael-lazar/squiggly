.PHONY: clean publish test lint

dist:
	python setup.py sdist --formats=gztar,zip
	python setup.py bdist_wheel --python-tag=py3

publish:
	twine upload dist/*.tar.gz dist/*.whl

test:
	env PYTHONPATH=. pytest -v tests/

lint:
	black --line-length 100 -t py37 setup.py tests squiggly
	isort -y -rc setup.py tests squiggly
	flake8 --max-line-length=100 --ignore=E203 setup.py test squiggly

clean:
	find . -name "*pyc" | xargs rm -rf $1
	rm -rf build dist *.egg-info
