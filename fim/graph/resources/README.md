# Property Graphs for Resource Descriptions

## Overview

These modules are intended to implement model manipulations for representations of physical resources:

- Description of AM resources (ARM models) and its update lifecycle based on reservations
- Description of resources delegated from AM to Broker (ADM models)
- Creation of combined broker model (CBM) showing all available resources and its'
update lifecycle based on reservations
- Creation of query responses to Orchestrators (BQM) and embedding of slice requests in 
BQM.


## AM Models

Basic operations on AM resource models (ARM) include
- Loading and validating a model according to ARM rules
- Updating a model (create/delete) from sliver information
- Partitioning ARM into one or more delegation models (ADMs)

Calendar support - ARMs or ADMs don't use calendars.

## Broker Models

Basic operations on Broker models include

- Receiving and validating ADMs from AMs
- Stitching multiple ADMs into a combined CBM model
- Updating CBM based on (create/delete) sliver information
- Matching queries to CBM and creating responses for Orchestrator (BQM models)

CBMs require a calendar (per resource). 

BQM can be based on a time query. Some queries might return the entire calendar to help Orchestrator 
make a decision

Multiple query types possible:
- Timed (including starting now as the default) - returns availability information without calendar. 
Calendar information needs to be serializable into FIM in this case. 
- Not-timed - returns calendar information.

## Linking relational database reservation information to graph models

Two IDs should play a role:

- Resource ID (a GUID)
- Reservation ID (also a GUID)

