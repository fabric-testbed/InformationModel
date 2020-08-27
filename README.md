# Information Model
FABRIC Information Model library, containing class definitions and methods for operating
on different types of information model representations (sliver and slice)

## Development environment

The recommended way is to set up your development environment using virtualenv after checking
out the code:
```bash
$ git clone git@github.com:fabric-testbed/InformationModel.git
$ cd InformationModel
$ mkvirtualenv -r requirements.txt infomodel
$ workon infomodel
(infomodel) $

```

## Installation

Multiple installation options possible. For CF development the recommended method is to
install from GitHub MASTER branch:
```bash
$ pip install git+https://github.com/fabric-testbed/InformationModel.git
```

For developing and testing the FIM code itself use editable install (from top-level directory)
```bash
(infomodel) $ pip install -e .
```

For inclusion in tools, etc, use PyPi
```bash
$ pip install fabric-fim
```

## Using fim_util.py utility

The utility supports a number of operations on GraphML files - enumerating nodes (for graphs)
coming out of yEd, loading into an instance of Neo4j, deleting graphs from Neo4j.

Start the [Neo4j-APOC docker container](https://github.com/fabric-testbed/fabric-docker-images/tree/master/neo4j-apoc)

Create fim_config.yaml with the following structure under `util/`:
```
# default fim_config configuration file for FIM utilities
neo4j:
  url: neo4j://0.0.0.0:7687
  user: neo4j
  pass: password
  import_host_dir: /host/directory/seen/by/neo4j/docker/as/imports
  import_dir: /imports
```
Run the utility for detailed help for the various operations:
```
(infomodel) $ python fim_util.py -h
```

## Code structure and imports

Base classes are under `fim.graph` and `fim.slivers` modules. 