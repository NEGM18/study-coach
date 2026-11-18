# Spot check: 20 processed rows vs raw (issue #19)

Sampled with seed 42 from `ml/data/processed/knowledge/kt_processed_v1.parquet`.

| user_id (hashed) | topic_id | question_id | is_correct | response_time_ms | raw order_id | result |
| --- | --- | --- | --- | --- | --- | --- |
| 92613ff5ce20a128 | 125 | 49301 | True | 49964 | 38242113 | ok |
| 596d86f7c30dc036 | 139 | 94092 | False | 2296 | 34744637 | ok |
| 64c9d28b95d8ac06 | 41 | 53975 | True | 4393 | 36467539 | ok |
| c603c19a03d451ff | 13 | 57494 | False | 15207 | 27848749 | ok |
| 0e4734745271e3a9 | 130 | 93301 | True | 12922 | 21956254 | ok |
| fceed5d8e2c2e926 | 103 | 85925 | True | 7346 | 22442700 | ok |
| 5ff3e8eaf74fc2e7 | 45 | 86544 | False | 37640 | 31353524 | ok |
| b01c52811ec288e6 | 63 | 89799 | True | 52402 | 38166752 | ok |
| a2bd385eb58e3514 | 56 | 58560 | True | 29796 | 30049170 | ok |
| 35ac8948309ccd2a | 98 | 75606 | False | 28222 | 38171997 | ok |
| ed678db9f1c5436d | 103 | 85869 | True | 33239 | 21981405 | ok |
| e480ad4b7fbbca2a | 111 | 53285 | True | 7976 | 24336933 | ok |
| 6e252b9361ca24ba | 108 | 85718 | True | 11047 | 29399075 | ok |
| aedca006e3472fca | 34 | 89130 | True | 89649 | 29513313 | ok |
| 24f82c7e04c5ba06 | 127 | 60141 | False | 65047 | 31496592 | ok |
| 4c2fa6f504f38754 | 97 | 51336 | True | 238227 | 35768236 | ok |
| 4b31f0af9cf80541 | 103 | 86080 | True | 10523 | 22387504 | ok |
| e4a5cf442ea1d1ca | 117 | 56093 | False | 2016 | 30333162 | ok |
| 396a1aa63bccf5ff | 58 | 93372 | False | 211278 | 24332484 | ok |
| 9b6d51f5379bdac2 | 45 | 86751 | True | 43000 | 26048111 | ok |

**Result: 20/20 rows found unchanged in the raw file.**
