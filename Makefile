# Makefile.include should set the WEBTOP variable to the location to install to
include Makefile.include

.PHONY: test install

test:
	pytest
	flake8 --ignore=E402,W503 .

install::
	mkdir -p ${WEBTOP}/systems/templates
	mkdir -p ${WEBTOP}/static/images
	cp systems/*.py ${WEBTOP}/systems/
	cp systems/templates/*.html ${WEBTOP}/systems/templates/
	cp static/*.{css,js} ${WEBTOP}/static/
	cp static/images/*.png ${WEBTOP}/static/images/
	echo "import sys; sys.path.insert(0, '${WEBTOP}')" > ${WEBTOP}/systems.wsgi
	echo "from systems import app as application" >> ${WEBTOP}/systems.wsgi
	@echo "Do not edit files in this directory!" > ${WEBTOP}/README
	@echo "Edit the originals and use 'make' to install them here" >> ${WEBTOP}/README
