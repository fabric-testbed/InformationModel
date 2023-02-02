import setuptools
from fim import __VERSION__

with open("README.md", "r") as fh:
  long_description = fh.read()

with open("requirements.txt", "r") as fh:
  install_requires = fh.read()

setuptools.setup(
  name="fabric_fim",
  version=__VERSION__,
  author="Ilya Baldin, Komal Thareja",
  description="FABRIC Information Model Library",
  url="https://github.com/fabric-testbed/InformationModel",
  long_description=long_description,
  long_description_content_type="text/markdown",
  packages=setuptools.find_packages(),
  include_package_data=True,
  scripts=['util/fim_util.py'],
  classifiers=[
    "Programming Language :: Python :: 3",
    "License :: OSI Approved :: MIT License",
    "Operating System :: OS Independent",
  ],
  python_requires=">=3.7",
  install_requires=install_requires,
  setup_requires=[
    "setuptools>=65.4.1",
    "wheel>=0.37.1",
  ],
)
