import utils

utils.set_search_paths(__file__)
import systems

sys1 = utils.MockSystem(name="sys1", repo="repo1", title="sys1 title",
                        pmid="1234", prereqs=["modeller", "python/scikit"],
                        description="sys1 desc", homepage="sys1 home")


def test_summary():
    """Test the summary page"""
    with utils.mock_systems(systems.app, [sys1]):
        c = systems.app.test_client()
        rv = c.get('/')
