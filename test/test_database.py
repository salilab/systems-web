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
sys3 = utils.MockSystem(name="fly_genome", repo="repo3", title="sys3 title",
                        pmid="5679", prereqs=["modeller", "python/scikit"],
                        description="sys3 desc", homepage="sys3 home",
                        tags=["foo", "bar"],
                        authors=["Smith J", "Jones A", "Jones B"],
                        journal="Nature", volume="99", pubdate="2014 Dec",
                        accessions=['PDBDEV_00000001', 'foo'],
                        github_url='ghurl', github_branch='ghbranch')
sys4 = utils.MockSystem(name="sys4", repo="repo4", title="sys4 title",
                        pmid="5679", prereqs=["modeller", "python/protobuf"],
                        description="sys4 desc", homepage="sys4 home",
                        tags=["foo", "bar"],
                        authors=["Smith J", "Jones A", "Jones B"],
                        journal="Nature", volume="99", pubdate="2014 Dec",
                        accessions=['PDBDEV_00000001', 'foo'],
                        github_url='ghurl', github_branch='ghbranch')


def test_test_class():
    """Test the Test class"""
    with systems.app.app_context():
        t = systems.database.Test(name='foo', retcode=42, stderr='bar',
                                  runtime=99)
        assert t.name == 'foo'
        assert t.retcode == 42
        assert t.stderr == 'bar'
        assert t.runtime == 99


def test_system_class():
    """Test the System class"""
    with utils.mock_systems(systems.app, [sys1, sys2, sys3, sys4]):
        with systems.app.app_context():
            s, s2, s3, s4 = systems.get_all_systems()
        for i in range(2):  # 2nd run should hit cache in most cases
            assert s.name == 'sys1'
            assert s.repo == 'repo1'
            assert s.title == 'sys1 title'
            assert s.pmid == '1234'
            assert s.description == 'sys1 desc'
            assert s.homepage == 'sys1 home'
            assert s.tags == ["foo", "bar"]
            assert s.pubmed_title == 'Smith J. Nature 99, 2014'
            assert s.accessions == ['PDBDEV_00000001', 'foo']
            assert s.pdbdev_accessions == ['PDBDEV_00000001']
            assert s.module_prereqs == ['imp', 'modeller', 'python3/scikit']
            assert s.conda_prereqs == ['imp', 'modeller', 'scikit-learn']
            assert s.readme == u'foobar'
            assert s2.readme == ''
            assert s2.pmid is None
            assert s2.pubmed_title is None
            assert s3.pubmed_title == 'Smith J, Jones A et al. Nature 99, 2014'
            assert s3.homepage == 'https://integrativemodeling.org/systems/22'
            # fly_genome system must use Python 2
            assert s3.name == "fly_genome"
            assert s3.module_prereqs == ['imp', 'modeller', 'python2/scikit']
            # protobuf must use Python 2
            assert s4.module_prereqs == ['imp', 'modeller', 'python2/protobuf']
