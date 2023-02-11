from pathlib import Path
from setuptools import setup, find_packages

VERSION = "1.0.2"
DESCRIPTION = "Timer Module with profiling features"

root = Path(__file__).parent
long_description = (root / "README.md").read_text()

setup(
    name="timer-module",
    author="syn-chromatic",
    author_email="synchromatic.github@gmail.com ",
    url="https://github.com/syn-chromatic/timer-module",
    version=VERSION,
    description=DESCRIPTION,
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(exclude=["examples"]),
    python_requires=">=3.10",
    install_requires=["setuptools>=45.0"],
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Programming Language :: Python :: 3.10",
        "Topic :: Utilities",
    ],
)
