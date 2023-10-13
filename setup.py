from re import search

from setuptools import find_packages, setup

install_requires = [
    "graphql-core>=3.2,<3.3",
    "typing-extensions>=4,<5",
]

tests_requires = [
    "pytest>=7.2,<8",
    "pytest-asyncio>=0.20,<1",
    "pytest-cov>=4,<5",
    "Jinja2>=3.1,<4",
    "sanic-testing>=22.3,<24",
]

dev_requires = [
    "flake8>=6,<7",
    "isort>=5,<6",
    "black>=23.9,<23.10",
    "mypy>=1.6,<1.7",
    "check-manifest>=0.47,<1",
] + tests_requires

install_flask_requires = [
    "flask>=1,<4",
]

install_sanic_requires = [
    "sanic>=21.12,<24",
]

install_webob_requires = [
    "webob>=1.8.7,<2",
]

install_aiohttp_requires = [
    "aiohttp>=3.8,<4",
]

install_quart_requires = ["quart>=0.15,<1"]

install_all_requires = (
    install_requires
    + install_flask_requires
    + install_sanic_requires
    + install_webob_requires
    + install_aiohttp_requires
    + install_quart_requires
)

with open("graphql_server/version.py") as version_file:
    version = search('version = "(.*)"', version_file.read()).group(1)

with open("README.md", encoding="utf-8") as readme_file:
    readme = readme_file.read()

setup(
    name="graphql-server",
    version=version,
    description="GraphQL Server tools for powering your server",
    long_description=readme,
    long_description_content_type="text/markdown",
    url="https://github.com/graphql-python/graphql-server",
    download_url="https://github.com/graphql-python/graphql-server/releases",
    author="Syrus Akbary",
    author_email="me@syrusakbary.com",
    license="MIT",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: MIT License",
    ],
    keywords="api graphql protocol rest",
    packages=find_packages(include=["graphql_server*"]),
    install_requires=install_requires,
    tests_require=install_all_requires + tests_requires,
    extras_require={
        "all": install_all_requires,
        "test": install_all_requires + tests_requires,
        "dev": install_all_requires + dev_requires,
        "flask": install_flask_requires,
        "sanic": install_sanic_requires,
        "webob": install_webob_requires,
        "aiohttp": install_aiohttp_requires,
        "quart": install_quart_requires,
    },
    include_package_data=True,
    zip_safe=False,
    platforms="any",
)
