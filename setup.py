#!/usr/bin/env python3
import setuptools

with open("README.md", "rt") as readme_fp:
    long_description = readme_fp.read().strip()


setuptools.setup(
    name="pytracer",
    version="0.0.3",
    description="Prints function calls of the Python program",
    long_description=long_description,
    url="https://github.com/alexbers/pytracer",
    author="Alexander Bersenev",
    author_email="bay@hackerdom.ru",
    maintainer="Alexander Bersenev",
    maintainer_email="bay@hackerdom.ru",
    license="MIT",
    py_modules=["pytracer"],
    scripts=[
        "pytracer.py", "pytracer"
    ],
    classifiers=[
        "Intended Audience :: Information Technology",
        "Intended Audience :: System Administrators",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7"
    ]
)
