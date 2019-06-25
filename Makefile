# Makefile.include should set the WEBTOP variable to the location to install to
include Makefile.include

.PHONY: test install

test:
	py.test --pep8

install::
	mkdir -p ${WEBTOP}/systems/templates
	mkdir -p ${WEBTOP}/images
	cp systems/*.py ${WEBTOP}/systems/
	cp systems/templates/*.html ${WEBTOP}/systems/templates/
	cp images/*.png ${WEBTOP}/images/
	echo "import sys; sys.path.insert(0, '${WEBTOP}')" > ${WEBTOP}/systems.wsgi
	echo "from systems import app as application" >> ${WEBTOP}/systems.wsgi
