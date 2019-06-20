import utils

utils.set_search_paths(__file__)
import systems

sys1 = utils.MockSystem(name="sys1", repo="repo1", title="sys1 title",
                        pmid="1234", prereqs=["modeller", "python/scikit"],
                        description="sys1 desc", homepage="sys1 home")


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


def test_summary():
    """Test the summary page"""
    with utils.mock_systems(systems.app, [sys1]):
        c = systems.app.test_client()
        rv = c.get('/')
        assert '<a class="sysmore" href="sys1 home">[more...]</a>' in rv.data
