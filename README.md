[![Requirements Status](https://requires.io/github/fabric-testbed/InformationModel/requirements.svg?branch=master)](https://requires.io/github/fabric-testbed/InformationModel/requirements/?branch=master)

[![PyPI](https://img.shields.io/pypi/v/fabric-fim?style=plastic)](https://pypi.org/manage/project/fabric-fim/releases/)

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

##  Graph models

Test graphs are located under [tests/models](tests/models). All graphs were created using 
[yEd](https://www.yworks.com/products/yed)
desktop graph editor (note that on-line version does not provide the same flexibility for creating custom node
and link properties).

## Testing

Run pytest

```bash
$ pytest [-s] test
```
Neo4j docker needs to be running to support tests of neo4j.

### Rules for creating new graphs

- Use [graph-template.graphml](test/models/graph-template.graphml) as a starter - copy it to a new name. 
The reason is yEd doesn't allow to save custom property schema separate from a graph and the template graph 
provides definitions for all custom node and edge properties. *Do not create a new graph from scratch as it 
will not have custom properties defined. Copying from a template graph into a new graph will lose properties*. 
- Use cut and paste from existing nodes in the template to build a new graph and fill in appropriate fields
using <right-click on node or edge>Properties | Data 
- Each node must have a Class and Type properties specified from 
[this document](https://docs.google.com/spreadsheets/d/1H9O7ptnODTpWvV2m2uTWQE34y1jleZIScEIh3B-_yS0/edit#gid=0).
Additional properties can be specified as needed in accordance with 
[this document](https://docs.google.com/document/d/1fmuUBVe_XWCJEI9zwImjFMBRFcRo-MZ9rUTWTu81atM/edit#heading=h.svpgmv6dph79).
- In general you don't need to assign NodeID properties on individual nodes, instead using [fim_util](util/README.md) 
to assign them, *however* when constructing linked models e.g. a site and a network AM advertisement that have 
nodes in common  (ConnectionPoints, SwitchFabrics etc), it is critical that same nodes appearing in both graphs 
carry the same NodeIDs, so those are best created in one graph and then cut-and-pasted in the other.  

## Graph validation

All graphs loaded into Neo4j (whether from files or being passed in as part of query or delegation) 
must conform to a set of rules expressed as Cypher queries. The basic set of rules for all 
types of graphs are located in [fim/graph/graph_validation_rules.json](fim/graph/data/graph_validation_rules.json).

Prior to ingestion graphs are also tested on general syntax validity of JSON-formatted fields.  

Additional rule files specific to model types may govern the validity of specific models.

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

## Neo4j Performance Considerations
For performance reasons it is critical that every instance of Neo4j has appropriate indexes created. 
Neo4j label `GraphNode` is hard-coded within FIM - every graph node has this label and another label is created
from the Class property and is meaningful to FIM. 
This is done for performance reasons to make it easier to create indexes and query models using those indexes.

The following indexes are required (can be created via script or through Neo4j console):
```
CREATE INDEX graphid FOR (n:GraphNode) ON (n.GraphID)
CREATE INDEX graphid_nodeid FOR (n:GraphNode) ON (n.GraphID, n.NodeID)
CREATE INDEX graphid_nodeid_type FOR (n:GraphNode) ON (n.GraphID, n.NodeID, n.Type)
CREATE INDEX graphid_type FOR (n:GraphNode) ON (n.GraphID, n.Type)
```
Available indexes can be checked via console by using the `:schema` command. 

An index can be dropped using the following command (substitute appropriate index name):
```
DROP INDEX graphid
```

See [additional documentation](https://neo4j.com/docs/cypher-manual/current/administration/indexes-for-search-performance/).
