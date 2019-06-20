import os
import sys
import flask
import contextlib
import tempfile
import shutil
import yaml
import json


# Make reading flask config a noop
def _mock_from_pyfile(self, fname, silent=False):
    pass
flask.Config.from_pyfile = _mock_from_pyfile


def set_search_paths(fname):
    """Set search paths so that we can import Python modules and use mocks"""
    # Path to mocks
    sys.path.insert(0, os.path.join(os.path.dirname(fname), 'mock'))
    # Path to top level
    sys.path.insert(0, os.path.join(os.path.dirname(fname), '..'))


class MockSystem(object):
    def __init__(self, name, repo, title, pmid, prereqs, description,
                 homepage, tags):
        self.name, self.repo = name, repo
        self.title, self.pmid, self.prereqs = title, pmid, prereqs
        self.description, self.homepage = description, homepage
        self.tags = tags

    def make_yaml(self, fname):
        data = {'title': self.title, 'pmid': self.pmid,
                'prereqs': self.prereqs, 'tags': self.tags}
        with open(fname, 'w') as fh:
            yaml.dump(data, fh)

    def make_json(self, fname):
        data = {'description': self.description, 'homepage': self.homepage}
        with open(fname, 'w') as fh:
            json.dump(data, fh)

    def __get_sql(self):
        return ('insert into sys_name (name, repo) values ("%s", "%s")'
                % (self.name, self.repo))
    sql = property(__get_sql)


@contextlib.contextmanager
def mock_systems(app, systems):
    systop = tempfile.mkdtemp()
    app.testing = True
    app.config['HOST'] = 'localhost'
    app.config['USER'] = 'testuser'
    app.config['PASSWORD'] = 'testpwd'
    dbsetup = ['create table sys_name (name text, repo text)']
    for s in systems:
        dbsetup.append(s.sql)
        os.mkdir(os.path.join(systop, s.name))
        s.make_yaml(os.path.join(systop, s.name, 'metadata.yaml'))
        s.make_json(os.path.join(systop, s.name, 'github.json'))
    app.config['DATABASE'] = dbsetup
    app.config['SYSTEM_TOP'] = systop
    yield
    shutil.rmtree(systop, ignore_errors=True)
