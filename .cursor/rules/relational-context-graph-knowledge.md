---
trigger: model_decision
description: When create, recall relational and context knowledge with different entities
---

when in need of system to local relational knowledge use this:
Knowledge Graph Memory Server
A basic implementation of persistent memory using a local knowledge graph. This lets Claude remember information about the user across chats.

Core Concepts
Entities
Entities are the primary nodes in the knowledge graph. Each entity has:

A unique name (identifier)
An entity type (e.g., "person", "organization", "event")
A list of observations
Example:

{ "name": "John_Smith", "entityType": "person", "observations": ["Speaks fluent Spanish"] }
Relations
Relations define directed connections between entities. They are always stored in active voice and describe how entities interact or relate to each other.

Example:

{ "from": "John_Smith", "to": "Anthropic", "relationType": "works_at" }
Observations
Observations are discrete pieces of information about an entity. They are:

Stored as strings
Attached to specific entities
Can be added or removed independently
Should be atomic (one fact per observation)
Example:

{ "entityName": "John_Smith", "observations": [ "Speaks fluent Spanish", "Graduated in 2019", "Prefers morning meetings" ] }
API
Tools
create_entities

Create multiple new entities in the knowledge graph
Input: entities (array of objects)
Each object contains:
name (string): Entity identifier
entityType (string): Type classification
observations (string[]): Associated observations
Ignores entities with existing names
create_relations

Create multiple new relations between entities
Input: relations (array of objects)
Each object contains:
from (string): Source entity name
to (string): Target entity name
relationType (string): Relationship type in active voice
Skips duplicate relations
add_observations

Add new observations to existing entities
Input: observations (array of objects)
Each object contains:
entityName (string): Target entity
contents (string[]): New observations to add
Returns added observations per entity
Fails if entity doesn't exist
delete_entities

Remove entities and their relations
Input: entityNames (string[])
Cascading deletion of associated relations
Silent operation if entity doesn't exist
delete_observations

Remove specific observations from entities
Input: deletions (array of objects)
Each object contains:
entityName (string): Target entity
observations (string[]): Observations to remove
Silent operation if observation doesn't exist
delete_relations

Remove specific relations from the graph
Input: relations (array of objects)
Each object contains:
from (string): Source entity name
to (string): Target entity name
relationType (string): Relationship type
Silent operation if relation doesn't exist
read_graph

Read the entire knowledge graph
No input required
Returns complete graph structure with all entities and relations
search_nodes

Search for nodes based on query
Input: query (string)
Searches across:
Entity names
Entity types
Observation content
Returns matching entities and their relations
open_nodes

Retrieve specific nodes by name
Input: names (string[])
Returns:
Requested entities
Relations between requested entities
Silently skips non-existent nodes