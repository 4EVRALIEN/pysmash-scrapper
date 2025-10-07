"""
Setup configuration for PySmash Scraper.
"""

from setuptools import find_packages, setup

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="pysmash-scraper",
    version="1.0.0",
    author="PySmash Team",
    author_email="team@pysmash.com",
    description="A comprehensive scraper for Smash Up! card game data",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/4EVRALIEN/pysmash-scrapper",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Games/Entertainment",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.9",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.0",
            "pytest-cov>=4.0",
            "pytest-asyncio>=0.21",
            "black>=23.0",
            "isort>=5.0",
            "flake8>=6.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "pysmash-scraper=scraper.cli:main",
        ],
    },
    include_package_data=True,
    package_data={
        "scraper": ["py.typed"],
    },
)