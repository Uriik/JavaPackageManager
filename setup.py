from setuptools import setup, find_packages

setup(
    name="jpkg",
    version="0.1.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "streamlit>=1.40.0",
        "lxml>=5.0.0",
        "requests>=2.32.0",
        "click>=8.1.0",
        "pydantic>=2.0.0",
        "litellm>=1.50.0",
        "ollama>=0.3.0",
    ],
    entry_points={
        "console_scripts": [
            "jpkg=jpkg.main:cli",
        ],
    },
)
