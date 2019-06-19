class Prerequisite(object):
    def __init__(self, name, url, conda_package, salilab_channel=False):
        self.name, self.url, self.conda_package = name, url, conda_package
        self.salilab_channel = salilab_channel


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
                                    'protobuf'),
    'python/biopython': Prerequisite('biopython', 'http://biopython.org/',
                                     'biopython'),
    'python/pyparsing': Prerequisite(
        'pyparsing',
        'https://pypi.python.org/pypi/pyparsing/2.0.3',
        'pyparsing'),
    'python/argparse': Prerequisite(
        'argparse', 'https://pypi.python.org/pypi/argparse', 'argparse'),
    'allosmod': Prerequisite('allosmod',
                             'https://github.com/salilab/allosmod-lib',
                             None, salilab_channel=True),
    'gcc': Prerequisite('gcc', 'https://gcc.gnu.org/', None)
}
