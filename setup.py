import setuptools

with open("README.md", "r") as fh:
  long_description = fh.read()

with open("AUTHORS", "r") as fh:
  authors = fh.read()

setuptools.setup(
  name="fim",
  version="0.1",
  author=authors,
  description="FABRIC Information Model Library",
  url="https://github.com/fabric-testbed/InformationModel",
  long_description=long_description,
  long_description_content_type="text/markdown",
  classifiers=[
    "Programming Language :: Python :: 3",
    "License :: OSI Approved :: MIT License",
    "Operating System :: OS Independent",
  ],
  python_requires=">=3.7",
)
