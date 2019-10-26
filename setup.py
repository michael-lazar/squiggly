import setuptools


def long_description():
    with open("README.md", encoding="utf8") as f:
        return f.read()


setuptools.setup(
    name='squiggly',
    version='0.0.1',
    description='A delightful terminal interface for tildes.net',
    long_description=long_description(),
    url='https://github.com/michael-lazar/squiggly',
    author='Michael Lazar',
    author_email='lazar.michael22@gmail.com',
    license='Floodgap Free Software License',
    keywords='terminal console tui curses',
    packages=['squiggly'],
    python_requires='>=3.7',
    install_requires=['urwid>=2.0.0', 'spinners', 'tildee'],
    extras_require={'test': ['pytest']},
    entry_points={'console_scripts': ['squiggly=squiggly.main:main']},
    classifiers=[
        'Intended Audience :: End Users/Desktop',
        'Environment :: Console :: Curses',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: POSIX',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Topic :: Terminals',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content :: Message Boards',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content :: News/Diary',
    ],
)