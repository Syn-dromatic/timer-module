from setuptools import setup, find_packages

VERSION = "1.0.0"
DESCRIPTION = "Timer Module with profiling features"

setup(
    name="timer-module",
    author="Synchromatic",
    author_email="synchromatic.github@gmail.com ",
    url="https://github.com/syn-chromatic",
    version=VERSION,
    description=DESCRIPTION,
    packages=find_packages(exclude=["examples"]),
    python_requires=">=3.10",
    install_requires=["setuptools>=45.0"],
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Programming Language :: Python :: 3.10",
        "Topic :: Utilities",
    ],
)
