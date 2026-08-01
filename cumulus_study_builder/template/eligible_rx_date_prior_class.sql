-- eligible_rx_date_prior_class. prior treatment classes before each line.
--
-- For each (subject, rx_class) line, the distinct set of OTHER classes whose
-- first exposure was strictly earlier. Supports "prior class exposure" and
-- step-up / top-down logic (e.g. conventional before advanced therapy). assumes
-- at least one rx class is defined via the study-variable skill.
CREATE  TABLE   {{ prefix }}__eligible_rx_date_prior_class AS
WITH lines AS (
    SELECT subject_ref, rx_class, rx_sequence_date
    FROM   {{ prefix }}__eligible_rx_date
)
SELECT  cur.subject_ref,
        cur.rx_class,
        cur.rx_sequence_date,
        COUNT(DISTINCT prior.rx_class)                          AS prior_class_count,
        ARRAY_JOIN(ARRAY_SORT(ARRAY_AGG(DISTINCT prior.rx_class)), '|') AS prior_class_list
FROM    lines AS cur
LEFT JOIN lines AS prior
       ON prior.subject_ref = cur.subject_ref
      AND prior.rx_sequence_date < cur.rx_sequence_date
      AND prior.rx_class <> cur.rx_class
GROUP BY cur.subject_ref, cur.rx_class, cur.rx_sequence_date
;
