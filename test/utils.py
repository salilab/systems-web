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
                 homepage, tags, authors, journal, volume, pubdate,
                 accessions, has_thumbnail=False):
        self.name, self.repo = name, repo
        self.title, self.pmid, self.prereqs = title, pmid, prereqs
        self.description, self.homepage = description, homepage
        self.tags = tags
        self.authors, self.journal, self.pubdate = authors, journal, pubdate
        self.volume = volume
        self.accessions = accessions
        self.has_thumbnail = has_thumbnail
        self.builds = {'master': [], 'develop': []}

    def add_build(self, branch, build_id, imp_date, imp_version,
                  imp_githash, retcode):
        build = {'id': build_id, 'imp_date': imp_date,
                 'imp_version': imp_version, 'imp_githash': imp_githash,
                 'retcode': retcode}
        self.builds[branch].append(build)

    def make_yaml(self, fname):
        data = {'title': self.title, 'pmid': self.pmid,
                'prereqs': self.prereqs, 'tags': self.tags,
                'accessions': self.accessions}
        with open(fname, 'w') as fh:
            yaml.dump(data, fh)

    def make_json(self, fname):
        data = {'description': self.description, 'homepage': self.homepage}
        with open(fname, 'w') as fh:
            json.dump(data, fh)

    def make_pubmed(self, fname):
        authors = [{'name': name, 'authtype': 'Author'}
                   for name in self.authors]
        pub = {'pubdate': self.pubdate, 'source': self.journal,
               'authors': authors, 'volume': self.volume}
        data = {'result': {"uids": [self.pmid], self.pmid: pub}}
        with open(fname, 'w') as fh:
            json.dump(data, fh)

    def make_thumbnail(self, fname):
        if self.has_thumbnail:
            with open(fname, 'w') as fh:
                pass  # dummy empty image

    def get_sql(self, id):
        yield ('insert into sys_name (id, name, repo) values (%d, "%s", "%s")'
               % (id, self.name, self.repo))
        for branch, builds in self.builds.items():
            for build in builds:
                yield ('insert into sys_build (id, imp_date, imp_githash, '
                       'imp_version, imp_branch) values (%d, "%s", "%s", '
                       '"%s", "%s")'
                       % (build['id'], build['imp_date'],
                          build['imp_githash'], build['imp_version'], branch))
                yield ('insert into sys_test (build, sys, retcode) values '
                       '(%d, %d, %d)'
                       % (build['id'], id, build['retcode']))


@contextlib.contextmanager
def mock_systems(app, systems):
    systop = tempfile.mkdtemp()
    app.testing = True
    app.config['HOST'] = 'localhost'
    app.config['USER'] = 'testuser'
    app.config['PASSWORD'] = 'testpwd'
    dbsetup = ['create table sys_name (id int primary key, '
               'name text, repo text)',
               'create table sys_test (build int, sys int, name int, '
               'retcode int, stderr text, runtime int)',
               'create table sys_build (id int primary key, imp_date text, '
               'imp_githash text, imp_version text, imp_branch text, '
               'modeller_version text)',
               'create table sys_info (build int, sys int, url txt, '
               'use_modeller bool, imp_build_type text)',
               'create table sys_test_name (sys int, id int, name text)']
    for i, s in enumerate(systems):
        dbsetup.extend(s.get_sql(i))
        os.mkdir(os.path.join(systop, s.name))
        s.make_yaml(os.path.join(systop, s.name, 'metadata.yaml'))
        s.make_json(os.path.join(systop, s.name, 'github.json'))
        s.make_pubmed(os.path.join(systop, s.name, 'pubmed.json'))
        s.make_thumbnail(os.path.join(systop, s.name, 'thumb.png'))
    app.config['DATABASE'] = dbsetup
    app.config['SYSTEM_TOP'] = systop
    yield
    shutil.rmtree(systop, ignore_errors=True)
