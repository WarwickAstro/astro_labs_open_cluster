import os
from setuptools import find_packages
from setuptools import setup
from open_clusters_version import VERSION

ROOT_DIRECTORY = os.path.dirname(os.path.abspath(__file__))
REQ_FILE = os.path.join(ROOT_DIRECTORY, "requirements.txt")

def get_reqs(req_file):
    """
    Get module dependencies from requirements.txt.
    """
    if not os.path.isfile(req_file):
        raise BaseException("No requirements.txt file found, aborting!")
    else:
        with open(req_file, 'r') as fr:
            requirements = fr.read().splitlines()
    return requirements

# Get the long description from the README file
with open(os.path.join(ROOT_DIRECTORY, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='openclusters',
    version=VERSION,
    description='Physics with astro lab photometry pipeline',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='James McCormac',
    author_email='j.j.mccormac@warwick.ac.uk',
    # You can just specify package directories manually here if your project is
    # simple. Or you can use find_packages().
    #
    # Alternatively, if you just want to distribute a single Python file, use
    # the `py_modules` argument instead as follows, which will expect a file
    # called `my_module.py` to exist:
    #
    py_modules=["reduce", "mkregions", "photometry"],
    #
    #packages=find_packages(),
    install_requires=get_reqs(REQ_FILE),
    include_package_data=True,
    classifiers=[  # Optional
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 3 - Alpha',

        # Indicate who your project is intended for
        'Intended Audience :: Developers',

        # Pick your license as you wish
        'License :: OSI Approved :: GNU General Public License (GPL)',

        # Specify the Python versions you support here. In particular, ensure
        # that you indicate whether you support Python 2, Python 3 or both.
        # These classifiers are *not* checked by 'pip install'. See instead
        # 'python_requires' below.
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
)
