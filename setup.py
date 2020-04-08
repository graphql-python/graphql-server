from setuptools import setup, find_packages

install_requires = [
    "graphql-core==3.1.0",
]

tests_requires = [
    "pytest>=5.3,<5.4",
    "pytest-cov>=2.8,<3",
]

dev_requires = [
    "flake8>=3.7,<4",
    "isort>=4,<5",
    "black==19.10b0",
    "mypy>=0.761,<0.770",
    "check-manifest>=0.40,<1",
] + tests_requires

setup(
    name="graphql-server-core",
    version="2.0.0",
    description="GraphQL Server tools for powering your server",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/graphql-python/graphql-server-core",
    download_url="https://github.com/graphql-python/graphql-server-core/releases",
    author="Syrus Akbary",
    author_email="me@syrusakbary.com",
    license="MIT",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "License :: OSI Approved :: MIT License",
    ],
    keywords="api graphql protocol rest",
    packages=find_packages(exclude=["tests"]),
    install_requires=install_requires,
    tests_require=tests_requires,
    extras_require={
        'test': tests_requires,
        'dev': dev_requires,
    },
    include_package_data=True,
    zip_safe=False,
    platforms="any",
)
