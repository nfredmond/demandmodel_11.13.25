"""
Setup script for Transportation Demand Model package
"""
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="transportation-demand-model",
    version="1.0.0",
    author="Transportation Demand Model Team",
    description="Transportation demand modeling with automatic Census API and OpenStreetMap data loading",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/transportation-demand-model",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: GIS",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "demand-model=run_model:main",
        ],
    },
    include_package_data=True,
    keywords="transportation demand model census openstreetmap gis planning",
    project_urls={
        "Documentation": "https://github.com/yourusername/transportation-demand-model",
        "Source": "https://github.com/yourusername/transportation-demand-model",
        "Bug Reports": "https://github.com/yourusername/transportation-demand-model/issues",
    },
)
