class Prerequisite(object):
    def __init__(self, name, url, conda_package, salilab_channel=False,
                 python2_only=False):
        self.name, self.url, self.conda_package = name, url, conda_package
        self.salilab_channel = salilab_channel
        self.python2_only = python2_only
        self.module_name = None  # filled in later


ALL_PREREQS = {
    'imp': Prerequisite('IMP', 'https://integrativemodeling.org/',
                        'imp', salilab_channel=True),
    'modeller': Prerequisite('MODELLER', 'https://salilab.org/modeller/',
                             'modeller', salilab_channel=True),
    'python/scikit': Prerequisite('scikit-learn',
                                  'http://scikit-learn.org/stable/',
                                  'scikit-learn'),
    'python/matplotlib': Prerequisite('matplotlib', 'http://matplotlib.org/',
                                      'matplotlib'),
    'python/numpy': Prerequisite('numpy', 'http://www.numpy.org/', 'numpy'),
    'python/scipy': Prerequisite('scipy', 'https://www.scipy.org/', 'scipy'),
    'python/protobuf': Prerequisite('protobuf',
                                    'https://github.com/google/protobuf',
                                    'protobuf', python2_only=True),
    'python/biopython': Prerequisite('biopython', 'http://biopython.org/',
                                     'biopython'),
    'python/pyparsing': Prerequisite(
        'pyparsing',
        'https://pypi.python.org/pypi/pyparsing/2.0.3',
        'pyparsing'),
    'python/argparse': Prerequisite(
        'argparse', 'https://pypi.python.org/pypi/argparse', 'argparse'),
    'python/pandas': Prerequisite(
        'pandas', 'https://pypi.python.org/pypi/pandas', 'pandas'),
    'allosmod': Prerequisite('allosmod',
                             'https://github.com/salilab/allosmod-lib',
                             None, salilab_channel=True),
    'gcc': Prerequisite('gcc', 'https://gcc.gnu.org/', None)
}

# Module name is the prereq key
for module_name, prereq in ALL_PREREQS.items():
    prereq.module_name = module_name
