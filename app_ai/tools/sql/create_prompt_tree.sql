CREATE TABLE IF NOT EXISTS public.prompt_tree (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    parent_id INT REFERENCES prompt_tree(id) ON DELETE CASCADE,
    metadata JSONB DEFAULT '{}'::jsonb
);
