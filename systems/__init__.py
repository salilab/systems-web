import json
import operator
import itertools
import logging.handlers
from flask import Flask, g, render_template, request, abort
from .database import get_all_systems, add_all_build_results, ALL_BRANCHES
from .app import app


@app.teardown_appcontext
def close_db(error):
    if hasattr(g, 'db_conn'):
        g.db_conn.close()


@app.template_filter('timeformat')
def timeformat_filter(t):
    if t < 120:
        return "%d seconds" % t
    t /= 60.
    if t < 120:
        return "%d minutes" % t
    t /= 60.
    if t < 48:
        return "%d hours" % t
    t /= 24.
    return "%d days" % t


@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500


@app.route('/')
def summary():
    only_tag = request.args.get('tag')
    all_sys = get_all_systems()
    tags = frozenset(itertools.chain.from_iterable(s.tags for s in all_sys))
    if only_tag:
        all_sys = [s for s in all_sys if only_tag in s.tags]
    add_all_build_results(all_sys)
    all_sys = sorted(all_sys, key=operator.attrgetter('name'))
    tested_sys = [s for s in all_sys if s.last_build_results]
    develop_sys = [s for s in all_sys if not s.last_build_results]
    return render_template('summary.html', tested_systems=tested_sys,
                           develop_systems=develop_sys,
                           tags=sorted(tags, key=lambda x: x.lower()),
                           only_tag=only_tag, top_level='summary')


@app.route('/all-builds')
def all_builds():
    all_sys = get_all_systems()
    add_all_build_results(all_sys)
    # Keep only systems with at least one build result, and sort by name
    all_sys = sorted((s for s in all_sys if s.last_build_results),
                     key=operator.attrgetter('name'))
    all_results = {}
    all_builds = {}
    for branch in ALL_BRANCHES:
        builds_by_id = {}
        results_by_id = {}
        for system in all_sys:
            for result in system.build_results[branch]:
                builds_by_id[result.build.id] = result.build
                all_results[(result.build.id, system.id)] = result
        all_builds[branch] = [build for (build_id, build)
                              in sorted(builds_by_id.items(),
                                        key=operator.itemgetter(0))]
    return render_template('all-builds.html', systems=all_sys,
                           builds=all_builds, results=all_results,
                           top_level="all_builds")


@app.route('/<int:system_id>')
def system_by_id(system_id):
    all_sys = get_all_systems(system_id)
    add_all_build_results(all_sys)
    if not all_sys:
        abort(404)
    return render_template('system.html', system=all_sys[0],
                           results=all_sys[0].last_build_results)


@app.route('/<int:system_id>/build/<int:build_id>')
def build_by_id(system_id, build_id):
    all_sys = get_all_systems(system_id)
    if not all_sys:
        abort(404)
    add_all_build_results(all_sys, build_id)
    # Should be exactly one build result
    results = list(itertools.chain.from_iterable(
        all_sys[0].build_results.values()))
    if len(results) != 1:
        abort(404)
    tests = results[0].get_tests()
    return render_template('build.html', system=all_sys[0], result=results[0],
                           tests=tests)


@app.route('/api/list')
def list_systems():
    def make_dict(s):
        return dict((k, getattr(s, k)) for k in ('name', 'repo', 'pmid',
                                                 'homepage', 'conda_prereqs'))
    # Cannot use jsonify here as it doesn't support lists in flask 0.10
    return app.response_class(
        json.dumps([make_dict(s) for s in get_all_systems()]),
        mimetype='application/json')
