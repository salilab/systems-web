[![Build Status](https://travis-ci.org/salilab/systems-web.svg?branch=master)](https://travis-ci.org/salilab/systems-web)
[![codecov](https://codecov.io/gh/salilab/systems-web/branch/master/graph/badge.svg)](https://codecov.io/gh/salilab/systems-web)

This is a simple [Flask](http://flask.pocoo.org/) application to manage
the list of applications of [IMP](https://integrativemodeling.org/) to
biological systems at https://integrativemodeling.org/systems/.

## Configuration

1. Create a file `Makefile.include` in the same directory as `Makefile` that
   sets the `WEBTOP` variable to a directory readable by Apache.

2. Create a configuration file `<WEBTOP>/instance/systems.cfg`. This should
   be readable only by Apache (since it contains passwords) and contain
   a number of key=value pairs:
   - `HOST`, `DATABASE`, `USER`, `PASSWORD`: parameters to connect to the
     MySQL server.
   - `SYSTEM_TOP`: directory containing metadata for each system (this is
     populated by the `util/update_metadata.py` script).
   - `MAIL_SERVER`, `MAIL_PORT`, `ADMINS`: host and port to connect to to
     send emails when the application encounters an error, and a Python
     list of users to notify.

## Apache setup

1. Install `mod_wsgi`.
2. Add `Alias` rules to the Apache configuration to point `/systems/static`
   to `<WEBTOP>/static` and `/systems/info` to `<SYSTEM_TOP>`.
3. Add a suitable `WSGIScriptAlias` rule to the Apache configuration pointing
   `/systems` to `<WEBTOP>/systems.wsgi`.

## Deployment

Use `make test` to test changes to the application, and `make install` to
deploy it (this will install the files to the `WEBTOP` directory).
