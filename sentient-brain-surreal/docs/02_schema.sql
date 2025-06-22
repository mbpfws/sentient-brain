-- SurrealDB schema for Sentient-Brain (v0.1)
-- Vector dim default 384; adjust if you switch embedding model

-- -------------------------------------------
-- 1. Code Layer
-- -------------------------------------------
DEFINE TABLE code_chunk SCHEMAFULL PERMISSIONS full;
DEFINE FIELD file_path        ON code_chunk TYPE string;
DEFINE FIELD node_type        ON code_chunk TYPE string;
DEFINE FIELD name             ON code_chunk TYPE string;
DEFINE FIELD content          ON code_chunk TYPE string;
DEFINE FIELD vector           ON code_chunk TYPE vector<F64, 384>;
DEFINE FIELD meta             ON code_chunk TYPE object OPTIONAL;
DEFINE FIELD ts               ON code_chunk VALUE time::now();

DEFINE INDEX code_vec_index   ON code_chunk FIELDS vector SEARCH ANALYZER cosine;
DEFINE INDEX code_path_index  ON code_chunk FIELDS file_path;

-- -------------------------------------------
-- 2. Docs Layer
-- -------------------------------------------
DEFINE TABLE document_chunk SCHEMAFULL PERMISSIONS full;
DEFINE FIELD source_uri       ON document_chunk TYPE string;
DEFINE FIELD content          ON document_chunk TYPE string;
DEFINE FIELD vector           ON document_chunk TYPE vector<F64, 384>;
DEFINE FIELD order            ON document_chunk TYPE number;
DEFINE FIELD headings         ON document_chunk TYPE array<string> OPTIONAL;
DEFINE FIELD meta             ON document_chunk TYPE object OPTIONAL;
DEFINE FIELD ts               ON document_chunk VALUE time::now();

DEFINE INDEX doc_vec_index    ON document_chunk FIELDS vector SEARCH ANALYZER cosine;

-- -------------------------------------------
-- 3. Knowledge Concepts
-- -------------------------------------------
DEFINE TABLE knowledge_concept SCHEMAFULL PERMISSIONS full;
DEFINE FIELD title            ON knowledge_concept TYPE string;
DEFINE FIELD summary          ON knowledge_concept TYPE string;
DEFINE FIELD vector           ON knowledge_concept TYPE vector<F64, 384>;
DEFINE FIELD concept_type     ON knowledge_concept TYPE string;
DEFINE FIELD tech_stack       ON knowledge_concept TYPE array<string> OPTIONAL;
DEFINE FIELD broader          ON knowledge_concept TYPE array<knowledge_concept> OPTIONAL;
DEFINE FIELD narrower         ON knowledge_concept TYPE array<knowledge_concept> OPTIONAL;
DEFINE FIELD related          ON knowledge_concept TYPE array<knowledge_concept> OPTIONAL;
DEFINE FIELD ts               ON knowledge_concept VALUE time::now();

DEFINE INDEX concept_vec_idx  ON knowledge_concept FIELDS vector SEARCH ANALYZER cosine;

-- -------------------------------------------
-- 4. Tasks / Plan Layer
-- -------------------------------------------
DEFINE TABLE task SCHEMAFULL PERMISSIONS full;
DEFINE FIELD title            ON task TYPE string;
DEFINE FIELD description      ON task TYPE string OPTIONAL;
DEFINE FIELD status           ON task TYPE string DEFAULT 'TODO';
DEFINE FIELD parent           ON task TYPE task OPTIONAL;
DEFINE FIELD ts               ON task VALUE time::now();

-- -------------------------------------------
-- 5. Chat Messages
-- -------------------------------------------
DEFINE TABLE chat_message SCHEMAFULL PERMISSIONS full;
DEFINE FIELD thread_id        ON chat_message TYPE string;
DEFINE FIELD role             ON chat_message TYPE string;
DEFINE FIELD content          ON chat_message TYPE string;
DEFINE FIELD vector           ON chat_message TYPE vector<F64, 384>;
DEFINE FIELD ts               ON chat_message VALUE time::now();

DEFINE INDEX chat_vec_index   ON chat_message FIELDS vector SEARCH ANALYZER cosine;
