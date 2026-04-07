from setuptools import find_packages, setup

from markio import __version__

setup(
    name="markio",
    version=__version__,
    packages=find_packages(),
    install_requires=[
        "mineru[all]",
        "pypandoc",
        "aiofiles",
        "aiohttp",
        "docling",
        "fastapi[standard]",
        "uvicorn[standard]",
        "python-multipart",
        "typer[all]",
        "fastapi-mcp",
    ],
    entry_points={
        "console_scripts": [
            "markio=markio.sdk.markio_cli:app",
        ],
    },
    include_package_data=True,
    description="Markio Document Parser CLI",
    author="SimonSun",
    author_email="",
    url="https://github.com/Tendo33/markio",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
