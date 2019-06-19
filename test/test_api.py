import utils
import json

utils.set_search_paths(__file__)
import systems

sys1 = utils.MockSystem(name="sys1", repo="repo1", title="sys1 title",
                        pmid="1234", prereqs=["modeller", "python/scikit"],
                        description="sys1 desc", homepage="sys1 home")


class Tests(object):
    def test_list(self):
        """Test the /api/list route"""
        with utils.mock_systems(systems.app, [sys1]):
            c = systems.app.test_client()
            rv = c.get('/api/list')
            # Should be a JSON string listing all systems
            assert '"homepage": "sys1 home"' in rv.data
            assert ('"conda_prereqs": ["modeller", "scikit-learn", "imp"]'
                    in rv.data)
            j = json.loads(rv.data)
            assert len(j) == 1
            assert j[0]['pmid'] == '1234'
