# Information Model
FABRIC Information Model library, containing class definitions and methods for operating
on different types of information model representations (sliver and slice)

## Development environment

The recommended way is to set up your development environment using `virtualenv` after checking
out the code:
```bash
$ git clone git@github.com:fabric-testbed/InformationModel.git
$ cd InformationModel
$ mkvirtualenv -r requirements.txt infomodel
$ workon infomodel
(infomodel) $
```

Note that the information model code depends on using the
 [Neo4j-APOC docker container](https://github.com/fabric-testbed/fabric-docker-images/tree/master/neo4j-apoc).
Follow the instructions with the container to start it. 

## Installation

Multiple installation options possible. For CF development the recommended method is to
[install from GitHub MASTER branch](https://codeinthehole.com/tips/using-pip-and-requirementstxt-to-install-from-the-head-of-a-github-branch/):
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

## Test graphs

Test graphs are located under [tests/models](tests/models). All graphs were created using [yEd](https://www.yworks.com/products/yed)
desktop graph editor (note that on-line version does not provide the same flexibility for creating custom node
and link properties).

## Graph validation

All graphs loaded into Neo4j (whether from files or being passed in as part of query or delegation) 
must conform to a set of rules expressed as Cypher queries. The basic set of rules for all 
types of graphs are located in [fim/graph/graph_validation_rules.json](fim/graph/data/graph_validation_rules.json).

Additional rule files may govern specific model types.

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
Parameters `password` and `import_host_dir` depend on how the Docker container is started in
the procedure above. Other parameters should remain unchanged from what is shown. 

Run the utility for detailed help for the various operations:
```
(infomodel) $ python fim_util.py -h
```

## Code structure and imports

Base classes are under `fim.graph` and `fim.slivers` modules. 