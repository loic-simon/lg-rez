import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = fh.readlines()

setuptools.setup(
    name="lg-rez",
    version="1.0.2",
    author="Loïc Simon, Tom Lacoma",
    author_email="loic.simon@espci.org, tom.lacoma@espci.org",
    description="Discord bot for organizing Werewolf RP games ESPCI-style",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/loic-simon/lg-rez",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    install_requires=requirements,
    python_requires='>=3.8',
)
