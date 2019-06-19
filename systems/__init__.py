import MySQLdb
import os
import json
import yaml
from flask import Flask, g
from .prerequisites import ALL_PREREQS

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


class System(object):
    def __init__(self, name, repo):
        self.name, self.repo = name, repo

    def _read_metadata(self):
        if not hasattr(self, '__metadata'):
            meta = os.path.join(app.config['SYSTEM_TOP'], self.name,
                                'metadata.yaml')
            with open(meta) as fh:
                self.__metadata = yaml.load(fh)
        return self.__metadata
    _metadata = property(_read_metadata)

    def _read_github(self):
        if not hasattr(self, '__github'):
            gh = os.path.join(app.config['SYSTEM_TOP'], self.name,
                              'github.json')
            with open(gh) as fh:
                j = json.load(fh)
            # Add markup where appropriate
            j['description'] = j['description'].replace(' FRETR ',
                                                        ' FRET<sub>R</sub> ')
            # Workaround broken repo info
            if self.name == 'fly_genome':
                j['homepage'] = \
                    'https://integrativemodeling.org/systems/?sys=22'
            self.__github = j
        return self.__github
    _github = property(_read_github)

    pmid = property(lambda self: self._metadata.get('pmid'))
    homepage = property(lambda self: self._github['homepage'])

    def __get_conda_prereqs(self):
        reqs = []
        for p in self._metadata.get('prereqs', []) + ['imp']:
            po = ALL_PREREQS[p]
            if po.conda_package:
                reqs.append(po.conda_package)
        return reqs
    conda_prereqs = property(__get_conda_prereqs)


def get_all_systems():
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT name, repo FROM sys_name')
    return [System(*x) for x in c]


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
