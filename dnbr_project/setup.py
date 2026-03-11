"""
Setup configuration for dNBR Burn Area Analysis package
"""
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="dnbr-burn-analysis",
    version="1.0.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="Automated burn area detection using Earth Engine and Otsu thresholding",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/dnbr-burn-analysis",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Scientific/Engineering :: GIS",
        "Topic :: Scientific/Engineering :: Image Processing",
    ],
    python_requires=">=3.8",
    install_requires=[
        "earthengine-api>=1.7.0",
        "geemap>=0.30.0",
        "numpy>=1.20.0",
        "matplotlib>=3.5.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0",
            "black>=22.0",
            "flake8>=4.0",
            "isort>=5.0",
        ],
    },
)
