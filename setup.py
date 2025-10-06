from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="pysmash-scraper",
    version="1.0.0",
    author="PySmash Scraper Team",
    author_email="contact@example.com",
    description="A comprehensive web scraping toolkit for Smash Up! card game data",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/pysmash-scraper",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Games/Entertainment",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "pysmash-scraper=scraper.cli:main",
        ],
    },
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
            "pytest-asyncio>=0.21.0",
            "flake8>=6.0.0",
            "black>=23.0.0",
            "isort>=5.12.0",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)
