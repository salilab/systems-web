import utils

utils.set_search_paths(__file__)
from systems import prerequisites


def test_prerequisites():
    """Test the ALL_PREREQS dict"""
    imp = prerequisites.ALL_PREREQS['imp']
    assert imp.name == 'IMP'
    assert imp.conda_package == 'imp'
    assert imp.salilab_channel is True
