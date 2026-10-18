# Observations

`observations.csv` — the minimum observation metadata ledger (schema in docs/PROTOCOL.md §9):

observation_id, entity_id, state_id, metric, value, unit, source_url, publisher,
publication_date, measurement_window, geography, sample_size, quality_class,
missingness_type, retrieved_at, notes

Every non-imputed value used anywhere downstream should trace back to a row here.
