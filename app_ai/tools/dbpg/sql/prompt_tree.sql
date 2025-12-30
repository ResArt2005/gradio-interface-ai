CREATE TABLE IF NOT EXISTS public.prompt_tree (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    parent_id INT REFERENCES prompt_tree(id) ON DELETE CASCADE,
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Создаем индекс для ускорения запросов по parent_id
CREATE INDEX IF NOT EXISTS idx_prompt_tree_parent_id ON public.prompt_tree(parent_id);