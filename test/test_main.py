import utils

utils.set_search_paths(__file__)
import systems

sys1 = utils.MockSystem(name="sys1", repo="repo1", title="sys1 title",
                        pmid="1234", prereqs=["modeller", "python/scikit"],
                        description="sys1 desc", homepage="sys1 home",
                        tags=["foo", "bar"], authors=["Smith J"],
                        journal="Nature", volume="99", pubdate="2014 Dec")
sys2 = utils.MockSystem(name="sys2", repo="repo2", title="sys2 title",
                        pmid="5678", prereqs=["modeller", "python/scikit"],
                        description="sys2 desc", homepage="sys2 home",
                        tags=["foo", "baz"],
                        authors=["Smith J", "Jones A", "Jones B"],
                        journal="Nature", volume="99", pubdate="2014 Dec",
                        has_thumbnail=True)
sys2.add_build('master', 1, imp_date="2019-06-15", imp_version="2.11.0",
               imp_githash="2a", retcode=0)
sys2.add_build('develop', 2, imp_date="2019-06-15", imp_version=None,
               imp_githash="3a", retcode=0)
sys2.add_build('develop', 3, imp_date="2019-07-15", imp_version=None,
               imp_githash="4a", retcode=1)


def test_system_class():
    """Test the System class"""
    with utils.mock_systems(systems.app, [sys1]):
        with systems.app.app_context():
            s, = systems.get_all_systems()
        assert s.name == 'sys1'
        assert s.repo == 'repo1'
        assert s.title == 'sys1 title'
        assert s.pmid == '1234'
        assert s.description == 'sys1 desc'
        assert s.homepage == 'sys1 home'
        assert s.tags == ["foo", "bar"]
        assert s.pubmed_title == 'Smith J. Nature 99, 2014'


def test_summary_all_tags():
    """Test the summary page with all tags shown"""
    with utils.mock_systems(systems.app, [sys1, sys2]):
        c = systems.app.test_client()
        rv = c.get('/')
        assert '<a class="sysmore" href="sys1 home">[more...]</a>' in rv.data
        assert '<a class="sysmore" href="sys2 home">[more...]</a>' in rv.data
        assert '<a class="tag" href="?tag=foo">foo</a>' in rv.data
        assert '<a class="tag" href="?tag=bar">bar</a>' in rv.data
        assert '<a class="tag" href="?tag=baz">baz</a>' in rv.data
        assert ('<img src="//integrativemodeling.org/systems/sys2/thumb.png"'
                in rv.data)


def test_summary_only_tags():
    """Test the summary page with only one tag shown"""
    with utils.mock_systems(systems.app, [sys1, sys2]):
        c = systems.app.test_client()
        rv = c.get('/?tag=bar')
        assert '<a class="sysmore" href="sys1 home">[more...]</a>' in rv.data
        assert ('<a class="sysmore" href="sys2 home">[more...]</a>'
                not in rv.data)
        assert '<a class="tag" href="?tag=foo">foo</a>' in rv.data
        assert '<a class="tag" href="?tag=bar">bar</a>' in rv.data
        assert '<a class="tag" href="?tag=baz">baz</a>' in rv.data
