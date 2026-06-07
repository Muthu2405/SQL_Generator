"""Package setup for sqlgen — installable via ``pip install -e .``."""

from setuptools import setup, find_packages

setup(
    name="sqlgen",
    version="0.1.0",
    description="Convert natural-language questions into SQL using Anthropic Claude.",
    author="sqlgen contributors",
    python_requires=">=3.9",
    packages=find_packages(exclude=("tests", "tests.*")),
    install_requires=[
        "anthropic>=0.39.0",
        "rich>=13.7.0",
        "fastapi>=0.110.0",
        "uvicorn>=0.28.0",
        "pydantic>=2.0",
    ],
    entry_points={
        "console_scripts": [
            "sqlgen=src/sql_generator.cli:main",
            "sqlgen-server=src/sql_generator.server:main",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3 :: Only",
    ],
)
