"""Setup configuration for Fastuner"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="fastuner",
    version="0.1.0",
    author="Javier Fernández Rico",
    description="One-Click Model Deployment & Fine-Tuning Service for AWS SageMaker",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/0xjav/Fastuner",
    packages=find_packages(exclude=["tests*", "infra*", "docker*"]),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.10",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "fastuner=fastuner.cli.main:cli",
        ],
    },
)
