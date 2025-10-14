CREATE TABLE IF NOT EXIST prompt_tree (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    parent_id INT REFERENCES tree_nodes(id) ON DELETE CASCADE,
    metadata JSONB DEFAULT '{}'::jsonb
);
