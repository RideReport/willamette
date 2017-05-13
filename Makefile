willamette.lambda.zip: *.py v/lib/python2.7/site-packages/* Makefile
	mkdir -p temp-packages
	pip install -r requirements.txt -t temp-packages/
	rm -f willamette.lambda.zip
	zip willamette.lambda.zip *.py *.wkt
	cd temp-packages && zip -pur ../willamette.lambda.zip *
	rm -r temp-packages
