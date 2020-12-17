import re
import setuptools


repo_url = "https://github.com/loic-simon/lg-rez"

version = ""
with open("lgrez/__init__.py") as f:
    version = re.search(r"""^__version__\s*=\s*['"](.*?)['"]""", f.read(), re.MULTILINE).group(1)

assert version, "__version__ not found in __init__.py"


def absolute_links(string, base):
    """Replace all relative Markdown links in <string> by absolute links with base <base>"""
    base = base.rstrip("/")
    return re.sub(
        r"\[(.+?)\]\(([^:]+?)\)",       # Matches every [text](link) patterns without ":" in link
        f"[\\1]({base}/\\2)",           # Replace link by base/link
        string
    )

with open("README.md", "r", encoding="utf-8") as fh:
    readme = fh.read()

version_blob_url = f"{repo_url}/blob/{version}"     # Github blob URL for tag <version>
long_description = absolute_links(readme, version_blob_url)
# long_description is README.md contents with relative links to project files/folders converted into links to files on GitHub blob, so they can be clicked on PyPI.


with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = fh.readlines()


setuptools.setup(
    name="lg-rez",
    version=version,
    author="Loïc Simon, Tom Lacoma",
    author_email="loic.simon@espci.org, tom.lacoma@espci.org",
    description="Discord bot for organizing Werewolf RP games ESPCI-style",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url=repo_url,
    packages=setuptools.find_packages(),        # ['lgrez', 'lgrez.blocs', 'lgrez.features']
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Framework :: AsyncIO",
        "Intended Audience :: Developers",
        "Natural Language :: French",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Games/Entertainment :: Role-Playing",
        "Topic :: Internet",
    ],
    install_requires=requirements,
    python_requires='>=3.8',
)
