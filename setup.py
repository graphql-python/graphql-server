from re import search
from setuptools import setup, find_packages

install_requires = ["graphql-core>=3.1.0,<4", "typing-extensions>=3.7.4,<4"]

tests_requires = [
    "pytest>=5.4,<5.5",
    "pytest-asyncio>=0.11.0",
    "pytest-cov>=2.8,<3",
    "aiohttp>=3.5.0,<4",
    "Jinja2>=2.10.1,<3",
]

dev_requires = [
    "flake8>=3.7,<4",
    "isort>=4,<5",
    "black==19.10b0",
    "mypy>=0.761,<0.770",
    "check-manifest>=0.40,<1",
] + tests_requires

install_flask_requires = [
    "flask>=0.7.0<1",
]

install_sanic_requires = [
    "sanic>=20.3.0,<21",
]

install_webob_requires = [
    "webob>=1.8.6,<2",
]

install_aiohttp_requires = [
    "aiohttp>=3.5.0,<4",
]

install_quart_requires = ["quart>=0.6.15,<1"]

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
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
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
