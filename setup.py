#!/usr/bin/env python3
"""HydraFlow AI - 九头蛇生成式工作流平台"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="hydraflow-ai",
    version="1.1.0",
    author="HydraFlow AI Team",
    author_email="dev@hydraflow.ai",
    description="九头蛇生成式工作流平台 - 多模态AI工作流编排引擎",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/hydraflow-ai/hydraflow",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Software Development :: Libraries :: Application Frameworks",
    ],
    python_requires=">=3.10",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.1.0",
            "black>=23.12.0",
            "flake8>=6.1.0",
            "mypy>=1.7.1",
            "isort>=5.13.0",
            "pre-commit>=3.6.0",
        ],
        "docs": [
            "mkdocs>=1.5.0",
            "mkdocs-material>=9.5.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "hydraflow=main:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.json", "*.md"],
        "hydraflow": [
            "../config/*.json",
            "../prompts/templates/*.md",
            "../docs/*.md",
        ],
    },
    zip_safe=False,
)