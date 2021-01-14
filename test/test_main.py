import utils

utils.set_search_paths(__file__)
import systems

sys1 = utils.MockSystem(name="sys1", repo="repo1", title="sys1 title",
                        pmid="1234", prereqs=["modeller", "python/scikit"],
                        description="sys1 desc", homepage="sys1 home",
                        tags=["foo", "bar"], authors=["Smith J"],
                        journal="Nature", volume="99", pubdate="2014 Dec",
                        accessions=['PDBDEV_00000001', 'foo'],
                        github_url='ghurl', github_branch='ghbranch',
                        readme='foobar')
sys2 = utils.MockSystem(name="sys2", repo="repo2", title="sys2 title",
                        pmid=None, prereqs=["modeller", "python/scikit"],
                        description="sys2 desc", homepage="sys2 home",
                        tags=["foo", "baz"],
                        authors=["Smith J", "Jones A", "Jones B"],
                        journal="Nature", volume="99", pubdate="2014 Dec",
                        accessions=[], has_thumbnail=True,
                        github_url='ghurl', github_branch='ghbranch')
sys2.add_build('main', 1, imp_date="2019-06-15", imp_version="2.11.0",
               imp_githash="2a", retcode=0, url='url1', use_modeller=True,
               imp_build_type='fast')
sys2.add_build('develop', 2, imp_date="2019-06-15", imp_version=None,
               imp_githash="3a", retcode=0, url='url2', use_modeller=True,
               imp_build_type='debug')
sys2.add_build('develop', 3, imp_date="2019-07-15", imp_version=None,
               imp_githash="4a", retcode=1, url='url3', use_modeller=False,
               imp_build_type='release')


def test_summary_all_tags():
    """Test the summary page with all tags shown"""
    with utils.mock_systems(systems.app, [sys1, sys2]):
        c = systems.app.test_client()
        rv = c.get('/')
        assert b'<a class="sysmore" href="sys1 home">[more...]</a>' in rv.data
        assert b'<a class="sysmore" href="sys2 home">[more...]</a>' in rv.data
        assert b'<a class="tag" href="?tag=foo">foo</a>' in rv.data
        assert b'<a class="tag" href="?tag=bar">bar</a>' in rv.data
        assert b'<a class="tag" href="?tag=baz">baz</a>' in rv.data
        assert (b'<img src="//integrativemodeling.org/systems/info/'
                b'sys2/thumb.png"' in rv.data)


def test_summary_only_tags():
    """Test the summary page with only one tag shown"""
    with utils.mock_systems(systems.app, [sys1, sys2]):
        c = systems.app.test_client()
        rv = c.get('/?tag=bar')
        assert b'<a class="sysmore" href="sys1 home">[more...]</a>' in rv.data
        assert (b'<a class="sysmore" href="sys2 home">[more...]</a>'
                not in rv.data)
        assert b'<a class="tag" href="?tag=foo">foo</a>' in rv.data
        assert b'<a class="tag" href="?tag=bar">bar</a>' in rv.data
        assert b'<a class="tag" href="?tag=baz">baz</a>' in rv.data


def test_all_builds():
    """Test the all-builds page"""
    with utils.mock_systems(systems.app, [sys1, sys2]):
        c = systems.app.test_client()
        rv = c.get('/all-builds')
        assert (b'<a class="buildbox build_fail" title="Build failed"'
                in rv.data)
        assert b'<a class="buildbox build_ok" title="Build OK"' in rv.data


def test_build_failed():
    """Test the build information page with a system that failed"""
    with utils.mock_systems(systems.app, [sys1, sys2]):
        c = systems.app.test_client()
        rv = c.get('/1/build/3')
        assert (b'was tested but <span class="build_fail">does not work'
                in rv.data)


def test_build_ok():
    """Test the build information page with a system that passed"""
    with utils.mock_systems(systems.app, [sys1, sys2]):
        c = systems.app.test_client()
        rv = c.get('/1/build/1')
        assert b'has been verified to work with:' in rv.data


def test_unknown_build():
    """Test the build information page with an unknown system/build"""
    with utils.mock_systems(systems.app, [sys1, sys2]):
        c = systems.app.test_client()
        rv = c.get('/1/build/100')
        assert rv.status_code == 404
        rv = c.get('/100/build/1')
        assert rv.status_code == 404


def test_system():
    """Test the system information page"""
    with utils.mock_systems(systems.app, [sys1, sys2]):
        c = systems.app.test_client()
        _ = c.get('/1')


def test_unknown_system():
    """Test the system information page given an unknown system ID"""
    with utils.mock_systems(systems.app, [sys1]):
        c = systems.app.test_client()
        rv = c.get('/100')
        assert rv.status_code == 404


def test_timeformat_filter():
    """Test the timeformat filter"""
    with systems.app.app_context():
        assert systems.timeformat_filter(50) == "50 seconds"
        assert systems.timeformat_filter(2110) == "35 minutes"
        assert systems.timeformat_filter(18030) == "5 hours"
        assert systems.timeformat_filter(2592000) == "30 days"


def test_500():
    """Test custom error handler for an internal error"""
    with utils.mock_systems(systems.app, [sys1]):
        c = systems.app.test_client()
        # Force an error
        systems.app.config['SYSTEM_TOP'] = '/not/exist'
        # Don't throw an exception but instead return a 500 HTTP response
        systems.app.testing = False
        rv = c.get('/')
        assert b'An unexpected error has occurred' in rv.data
        assert rv.status_code == 500


def test_badge_ok():
    """Test badge for an OK build"""
    with utils.mock_systems(systems.app, [sys2]):
        c = systems.app.test_client()
        rv = c.get('/0/badge.svg?branch=main')
        assert b'stable release-2.11.0-brightgreen.svg' in rv.data
        assert rv.status_code == 302


def test_badge_ok_master():
    """Test badge for an OK build using legacy 'master' branch"""
    with utils.mock_systems(systems.app, [sys2]):
        c = systems.app.test_client()
        rv = c.get('/0/badge.svg?branch=master')
        assert b'stable release-2.11.0-brightgreen.svg' in rv.data
        assert rv.status_code == 302


def test_badge_failed():
    """Test badge for a failed build"""
    with utils.mock_systems(systems.app, [sys1]):
        c = systems.app.test_client()
        rv = c.get('/0/badge.svg?branch=develop')
        assert b'nightly build-never-red.svg' in rv.data
        assert rv.status_code == 302


def test_badge_bad():
    """Test badges for bad system or branch"""
    with utils.mock_systems(systems.app, [sys1]):
        c = systems.app.test_client()
        rv = c.get('/9/badge.svg?branch=develop')
        assert rv.status_code == 404

        rv = c.get('/0/badge.svg?branch=foo')
        assert rv.status_code == 400


def test_badge_old():
    """Test redirect for old badge URL"""
    with utils.mock_systems(systems.app, [sys2]):
        c = systems.app.test_client()
        rv = c.get('/?sysstat=0&branch=main')
        assert b'"/0/badge.svg?branch=main"' in rv.data
        assert rv.status_code == 301


def test_badge_old_master():
    """Test redirect for old badge URL using legacy 'master' branch"""
    with utils.mock_systems(systems.app, [sys2]):
        c = systems.app.test_client()
        rv = c.get('/?sysstat=0&branch=master')
        assert b'"/0/badge.svg?branch=main"' in rv.data
        assert rv.status_code == 301
