import MySQLdb
import os
import json
import yaml
from flask import g, Markup
from .prerequisites import ALL_PREREQS
from .app import app


ALL_BRANCHES = ['main', 'develop']


def connect_db():
    conn = MySQLdb.connect(host=app.config['HOST'], user=app.config['USER'],
                           passwd=app.config['PASSWORD'],
                           db=app.config['DATABASE'])
    return conn


def get_db():
    """Open a new database connection if necessary"""
    if not hasattr(g, 'db_conn'):
        g.db_conn = connect_db()
    return g.db_conn


class Test(object):
    """Information about an individual test (see BuildResult.get_tests)"""
    def __init__(self, name, retcode, stderr, runtime):
        self.name, self.retcode = name, retcode
        self.stderr, self.runtime = stderr, runtime


class BuildResult(object):
    """The result of testing one System as part of a Build"""
    def __init__(self, build, passed, system):
        self.build, self.passed = build, passed
        self._system_id = system.id

    def get_tests(self):
        """Get detailed result information as a set of Test objects"""
        conn = get_db()
        c = MySQLdb.cursors.DictCursor(conn)
        c.execute("SELECT sys_test_name.name name,retcode,stderr,runtime "
                  "FROM sys_test,sys_test_name WHERE build=%s AND "
                  "sys_test.sys=%s AND sys_test_name.id=sys_test.name AND "
                  "sys_test_name.sys=%s",
                  (self.build.id, self._system_id, self._system_id))
        return [Test(**x) for x in c]

    @property
    def _info(self):
        if not hasattr(self, '_info_internal'):
            conn = get_db()
            c = MySQLdb.cursors.DictCursor(conn)
            c.execute("SELECT url,use_modeller,imp_build_type FROM sys_info "
                      "WHERE sys=%s AND build=%s",
                      (self._system_id, self.build.id))
            self._info_internal = c.fetchone()
        return self._info_internal

    url = property(lambda self: self._info['url'])
    use_modeller = property(lambda self: self._info['use_modeller'])
    imp_build_type = property(lambda self: self._info['imp_build_type'])


class Build(object):
    """A run over all Systems with a given configuration"""
    def __init__(self, id, imp_branch, imp_date, imp_version,
                 imp_githash, modeller_version):
        self.id, self.imp_branch = id, imp_branch
        self.imp_date, self.imp_version = imp_date, imp_version
        self.imp_githash = imp_githash
        self.modeller_version = modeller_version


class System(object):
    def __init__(self, id, name, repo):
        self.id, self.name, self.repo = id, name, repo
        # Use add_all_build_results() to fill in
        self.build_results = dict((branch, []) for branch in ALL_BRANCHES)

    @property
    def last_build_results(self):
        return dict((branch, results[-1])
                    for (branch, results) in self.build_results.items()
                    if results)

    @property
    def _metadata(self):
        if not hasattr(self, '_metadata_internal'):
            meta = os.path.join(app.config['SYSTEM_TOP'], self.name,
                                'metadata.yaml')
            with open(meta, encoding='utf-8') as fh:
                self._metadata_internal = yaml.safe_load(fh)
                if self._metadata_internal is None:
                    raise ValueError("Empty metadata for %s" % self.name)
        return self._metadata_internal

    @property
    def readme(self):
        if not hasattr(self, '_readme_internal'):
            readme = os.path.join(app.config['SYSTEM_TOP'], self.name,
                                  'readme.html')
            if os.path.exists(readme):
                with open(readme, 'rb') as fh:
                    self._readme_internal = fh.read().decode('utf-8')
            else:
                self._readme_internal = ''
        return self._readme_internal

    @property
    def _pubmed(self):
        if not hasattr(self, '_pubmed_internal'):
            pubmed = os.path.join(app.config['SYSTEM_TOP'], self.name,
                                  'pubmed.json')
            if os.path.exists(pubmed):
                with open(pubmed, encoding='utf-8') as fh:
                    self._pubmed_internal = json.load(fh)
            else:
                self._pubmed_internal = None
        return self._pubmed_internal

    @property
    def pubmed_title(self):
        p = self._pubmed
        if p:
            pmid = p['result']['uids'][0]
            ref = p['result'][pmid]

            authors = [x['name'] for x in ref['authors']
                       if x['authtype'] == 'Author']
            if len(authors) > 2:
                citation = ', '.join(authors[:2]) + ' et al.'
            else:
                citation = ', '.join(authors) + '.'

            return citation + ' %s %s, %s' % (ref['source'], ref['volume'],
                                              ref['pubdate'].split()[0])

    @property
    def _github(self):
        if not hasattr(self, '_github_internal'):
            gh = os.path.join(app.config['SYSTEM_TOP'], self.name,
                              'github.json')
            with open(gh, encoding='utf-8') as fh:
                j = json.load(fh)
            # Workaround broken repo info
            if self.name == 'fly_genome':
                j['homepage'] = \
                    'https://integrativemodeling.org/systems/22'
            self._github_internal = j
        return self._github_internal

    def has_thumbnail(self):
        """Return True iff a thumbnail for this system exists"""
        thumb = os.path.join(app.config['SYSTEM_TOP'], self.name, 'thumb.png')
        return os.path.exists(thumb)

    @property
    def description(self):
        # Make sure any existing HTML tags are escaped
        d = Markup.escape(self._github['description'])
        # Fix markup of FRET_R and mark as safe for Jinja
        return Markup(d.replace(u'FRETR', u'FRET<sub>R</sub>'))

    pmid = property(lambda self: self._metadata.get('pmid'))
    title = property(lambda self: self._metadata['title'])
    tags = property(lambda self: self._metadata.get('tags', []))
    homepage = property(lambda self: self._github['homepage'])
    accessions = property(lambda self: self._metadata.get('accessions', []))
    pdbdev_accessions = property(lambda self: [x for x in self.accessions
                                               if x.startswith('PDBDEV')])
    github_url = property(lambda self: self._github['html_url'])
    github_branch = property(lambda self: self._github['default_branch'])

    @property
    def prereqs(self):
        return [ALL_PREREQS[p]
                for p in ['imp'] + self._metadata.get('prereqs', [])]

    @property
    def module_prereqs(self):
        reqs = self.prereqs
        # Use Python 2 only for systems that don't work with Python 3 or
        # that use Python-2-only modules
        if (self.name in ('fly_genome', 'saxsmerge_benchmark')
                or any(p.python2_only for p in reqs)):
            return [p.module_name.replace('python/', 'python2/') for p in reqs]
        else:
            return [p.module_name.replace('python/', 'python3/') for p in reqs]

    @property
    def conda_prereqs(self):
        return [p.conda_package for p in self.prereqs if p.conda_package]


def get_all_systems(id=None):
    """Get a list of all systems, as System objects"""
    conn = get_db()
    c = conn.cursor()
    query = 'SELECT id, name, repo FROM sys_name'
    if id:
        query += ' WHERE id=%s'
        c.execute(query, (id,))
    else:
        c.execute(query)
    return [System(*x) for x in c]


def add_all_build_results(systems, build_id=None):
    """Add BuildResult information to the given list of System objects"""
    sys_by_id = dict((s.id, s) for s in systems)
    build_by_id = {}
    conn = get_db()
    c = MySQLdb.cursors.DictCursor(conn)
    args = []
    wheres = []
    if len(systems) == 1:
        wheres.append('sys=%s')
        args.append(systems[0].id)
    if build_id:
        wheres.append('build=%s')
        args.append(build_id)
    where = ('WHERE ' + ' AND '.join(wheres)) if wheres else ''
    c.execute('SELECT sys sys_id,build build_id,imp_branch,modeller_version,'
              'imp_date,imp_version,imp_githash,MAX(retcode) retcode FROM '
              'sys_test INNERT JOIN sys_build ON sys_build.id=build '
              '%s GROUP BY build_id,sys_id,imp_branch '
              'ORDER BY imp_date' % where, args)
    for row in c:
        system = sys_by_id.get(row['sys_id'])
        if system:
            build = build_by_id.get(row['build_id'])
            if build is None:
                build = Build(
                    id=row['build_id'], imp_branch=row['imp_branch'],
                    imp_date=row['imp_date'], imp_version=row['imp_version'],
                    imp_githash=row['imp_githash'],
                    modeller_version=row['modeller_version'])
                build_by_id[row['build_id']] = build
            result = BuildResult(build=build, passed=(row['retcode'] == 0),
                                 system=system)
            system.build_results[row['imp_branch']].append(result)
