"""
SQLAlchemy-Continuum
--------------------

Versioning and auditing extension for SQLAlchemy.
"""

from setuptools import setup, Command
import subprocess
import sys


class PyTest(Command):
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        errno = subprocess.call(['py.test'])
        raise SystemExit(errno)


extras_require = {
    'test': [
        'pytest>=2.3.5',
        'flexmock>=0.9.7',
        'psycopg2>=2.4.6',
        'PyMySQL==0.6.1',
        'six>=1.4.0'
    ],
    'flask': ['Flask>=0.9'],
    'flask-login': ['Flask-Login>=0.2.9'],
    'i18n': ['SQLAlchemy-i18n >= 0.8.2'],
}


# Add all optional dependencies to testing requirements.
for name, requirements in extras_require.items():
    if name != 'test':
        extras_require['test'] += requirements


setup(
    name='SQLAlchemy-Continuum',
    version='0.10.3',
    url='https://github.com/kvesteri/sqlalchemy-continuum',
    license='BSD',
    author='Konsta Vesterinen',
    author_email='konsta@fastmonkeys.com',
    description='Versioning and auditing extension for SQLAlchemy.',
    long_description=__doc__,
    packages=[
        'sqlalchemy_continuum',
        'sqlalchemy_continuum.ext'
    ],
    zip_safe=False,
    include_package_data=True,
    platforms='any',
    install_requires=[
        'SQLAlchemy>=0.9.3',
        'SQLAlchemy-Utils>=0.24.1',
        'inflection>=0.2.0',
        'ordereddict>=1.1'
        if sys.version_info[0] == 2 and sys.version_info[1] < 7 else ''
    ],
    extras_require=extras_require,
    cmdclass={'test': PyTest},
    classifiers=[
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ]
)
