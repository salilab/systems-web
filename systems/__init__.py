import MySQLdb
import os
import json
import yaml
import operator
import itertools
from flask import Flask, g, render_template, request, abort
from .prerequisites import ALL_PREREQS


ALL_BRANCHES = ['master', 'develop']

app = Flask(__name__, instance_relative_config=True)
app.config.from_pyfile('systems.cfg')


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


@app.teardown_appcontext
def close_db(error):
    if hasattr(g, 'db_conn'):
        g.db_conn.close()


class Test(object):
    """The result of testing one System as part of a Build"""
    def __init__(self, build, retcode):
        self.build, self.retcode = build, retcode


class Build(object):
    """A run over all Systems with a given configuration"""
    def __init__(self, id, imp_branch, imp_date, imp_version,
                 imp_githash):
        self.id, self.imp_branch = id, imp_branch
        self.imp_date, self.imp_version = imp_date, imp_version
        self.imp_githash = imp_githash


class System(object):
    def __init__(self, id, name, repo):
        self.id, self.name, self.repo = id, name, repo
        # Use add_all_tests() to fill in
        self.tests = dict((branch, []) for branch in ALL_BRANCHES)

    @property
    def last_tests(self):
        return dict((branch, tests[-1])
                    for (branch, tests) in self.tests.items() if tests)

    @property
    def _metadata(self):
        if not hasattr(self, '_metadata_internal'):
            meta = os.path.join(app.config['SYSTEM_TOP'], self.name,
                                'metadata.yaml')
            with open(meta) as fh:
                self._metadata_internal = yaml.safe_load(fh)
        return self._metadata_internal

    @property
    def _pubmed(self):
        if not hasattr(self, '_pubmed_internal'):
            pubmed = os.path.join(app.config['SYSTEM_TOP'], self.name,
                                  'pubmed.json')
            if os.path.exists(pubmed):
                with open(pubmed) as fh:
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
            with open(gh) as fh:
                j = json.load(fh)
            # Workaround broken repo info
            if self.name == 'fly_genome':
                j['homepage'] = \
                    'https://integrativemodeling.org/systems/?sys=22'
            self._github_internal = j
        return self._github_internal

    def has_thumbnail(self):
        """Return True iff a thumbnail for this system exists"""
        thumb = os.path.join(app.config['SYSTEM_TOP'], self.name, 'thumb.png')
        return os.path.exists(thumb)

    pmid = property(lambda self: self._metadata.get('pmid'))
    title = property(lambda self: self._metadata['title'])
    tags = property(lambda self: self._metadata.get('tags', []))
    homepage = property(lambda self: self._github['homepage'])
    description = property(lambda self: self._github['description'])
    accessions = property(lambda self: self._metadata.get('accessions', []))
    pdbdev_accessions = property(lambda self: [x for x in self.accessions
                                               if x.startswith('PDBDEV')])

    def __get_conda_prereqs(self):
        reqs = []
        for p in self._metadata.get('prereqs', []) + ['imp']:
            po = ALL_PREREQS[p]
            if po.conda_package:
                reqs.append(po.conda_package)
        return reqs
    conda_prereqs = property(__get_conda_prereqs)


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


def add_all_tests(systems):
    """Add Test information to the given list of System objects"""
    sys_by_id = dict((s.id, s) for s in systems)
    build_by_id = {}
    conn = get_db()
    c = MySQLdb.cursors.DictCursor(conn)
    c.execute('SELECT sys_name.id sys_id,sys_build.id build_id,imp_branch,'
              'imp_date,imp_version,imp_githash,retcode FROM '
              'sys_test,sys_name,sys_build WHERE sys_name.id=sys_test.sys '
              'AND sys_build.id=sys_test.build ORDER BY imp_date')
    for row in c:
        system = sys_by_id.get(row['sys_id'])
        if system:
            build = build_by_id.get(row['build_id'])
            if build is None:
                build = Build(
                    id=row['build_id'], imp_branch=row['imp_branch'],
                    imp_date=row['imp_date'], imp_version=row['imp_version'],
                    imp_githash=row['imp_githash'])
                build_by_id[row['build_id']] = build
            test = Test(build=build, retcode=row['retcode'])
            system.tests[row['imp_branch']].append(test)


@app.route('/')
def summary():
    only_tag = request.args.get('tag')
    all_sys = get_all_systems()
    tags = frozenset(itertools.chain.from_iterable(s.tags for s in all_sys))
    if only_tag:
        all_sys = [s for s in all_sys if only_tag in s.tags]
    add_all_tests(all_sys)
    all_sys = sorted(all_sys, key=operator.attrgetter('name'))
    tested_sys = [s for s in all_sys if s.last_tests]
    develop_sys = [s for s in all_sys if not s.last_tests]
    return render_template('summary.html', tested_systems=tested_sys,
                           develop_systems=develop_sys,
                           tags=sorted(tags, key=lambda x: x.lower()),
                           only_tag=only_tag, top_level='summary')


@app.route('/all-builds')
def all_builds():
    all_sys = get_all_systems()
    add_all_tests(all_sys)
    # Keep only systems with at least one test, and sort by name
    all_sys = sorted((s for s in all_sys if s.last_tests),
                     key=operator.attrgetter('name'))
    all_tests = {}
    all_builds = {}
    for branch in ALL_BRANCHES:
        builds_by_id = {}
        tests_by_id = {}
        for system in all_sys:
            for test in system.tests[branch]:
                builds_by_id[test.build.id] = test.build
                all_tests[(test.build.id, system.id)] = test
        all_builds[branch] = [build for (build_id, build)
                              in sorted(builds_by_id.items(),
                                        key=operator.itemgetter(0))]
    return render_template('all-builds.html', systems=all_sys,
                           builds=all_builds, tests=all_tests,
                           top_level="all_builds")


@app.route('/<int:system_id>')
def system_by_id(system_id):
    all_sys = get_all_systems(system_id)
    if not all_sys:
        abort(404)
    return render_template('system.html', system=all_sys[0])


@app.route('/<int:system_id>/build/<int:build_id>')
def build_by_id(system_id, build_id):
    all_sys = get_all_systems(system_id)
    if not all_sys:
        abort(404)
    return render_template('build.html', system=all_sys[0], build_id=build_id)


@app.route('/api/list')
def list_systems():
    def make_dict(s):
        return dict((k, getattr(s, k))
                    for k in ('name', 'repo', 'pmid', 'homepage',
                              'conda_prereqs'))
    # Cannot use jsonify here as it doesn't support lists in flask 0.10
    return app.response_class(
        json.dumps([make_dict(s) for s in get_all_systems()]),
        mimetype='application/json')


if __name__ == '__main__':
    app.run(debug=True)
