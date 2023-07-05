from pathlib import Path
from setuptools import setup, find_packages

VERSION = "1.3.0"
DESCRIPTION = "Timer Module with performance profiling features"

root = Path(__file__).parent
long_description = (root / "README.md").read_text(encoding="utf-8")

setup(
    name="timer-module",
    author="syn-chromatic",
    author_email="synchromatic.github@gmail.com",
    url="https://github.com/syn-chromatic/timer-module",
    version=VERSION,
    description=DESCRIPTION,
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    python_requires=">=3.10",
    install_requires=["setuptools>=45.0"],
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.10",
        "Topic :: Utilities",
    ],
)
