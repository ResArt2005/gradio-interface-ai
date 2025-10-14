WITH RECURSIVE public.tree AS (
    SELECT id, name, parent_id, 1 AS depth
    FROM tree_nodes
    WHERE parent_id IS NULL
    UNION ALL
    SELECT t.id, t.name, t.parent_id, tree.depth + 1
    FROM tree_nodes t
    JOIN tree ON t.parent_id = tree.id
)
SELECT * FROM tree ORDER BY depth, id;
