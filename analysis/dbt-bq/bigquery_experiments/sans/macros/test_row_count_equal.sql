{% test row_count_equal(model, compare_model) %}
WITH source_count AS (
    SELECT COUNT(*) AS cnt FROM {{ model }}
),
compare_count AS (
    SELECT COUNT(*) AS cnt FROM {{ compare_model }}
)
SELECT
    source_count.cnt AS source_cnt,
    compare_count.cnt AS compare_cnt
FROM source_count
CROSS JOIN compare_count
WHERE source_count.cnt != compare_count.cnt
{% endtest %}
