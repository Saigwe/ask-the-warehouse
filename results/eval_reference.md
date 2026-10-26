# Benchmark: reference mode

- Answerable questions correct: 44/44 (100%)
- Requests that must be refused, refused: 10/10 (100%)
- Latency per answer: p50 17 ms, p95 26 ms

| ID | Question | Correct | Latency (ms) | Refusal reason |
|---|---|:---:|---:|---|
| a01 | What was total net spend? | ✅ | 20 |  |
| a02 | How much new money was obligated (gross)? | ✅ | 17 |  |
| a03 | How much was de-obligated? | ✅ | 18 |  |
| a04 | How many contract actions were there? | ✅ | 20 |  |
| a05 | How many suppliers were active? | ✅ | 22 |  |
| a06 | What share of obligations was not competed? | ✅ | 16 |  |
| a07 | What share of obligations went to small businesses? | ✅ | 15 |  |
| a08 | What is the average obligation per obligating action? | ✅ | 14 |  |
| a09 | What is the de-obligation rate? | ✅ | 12 |  |
| a10 | How many obligating actions were there? | ✅ | 9 |  |
| a11 | Net spend by bureau | ✅ | 16 |  |
| a12 | Net spend by category | ✅ | 17 |  |
| a13 | Net spend by fiscal quarter | ✅ | 12 |  |
| a14 | Net spend by month | ✅ | 13 |  |
| a15 | Contract actions per fiscal quarter | ✅ | 13 |  |
| a16 | De-obligations by bureau | ✅ | 12 |  |
| a17 | Not-competed share by category | ✅ | 19 |  |
| a18 | Small-business share by bureau | ✅ | 18 |  |
| a19 | De-obligation rate by category | ✅ | 15 |  |
| a20 | Net spend by competition status | ✅ | 14 |  |
| a21 | Average obligation by bureau | ✅ | 14 |  |
| a22 | Not-competed share by fiscal quarter | ✅ | 14 |  |
| a23 | Net spend by business size | ✅ | 19 |  |
| a24 | Gross obligations by quarter of the calendar | ✅ | 14 |  |
| a25 | Which bureau had the most net spend? | ✅ | 23 |  |
| a26 | Which bureau had the least net spend? | ✅ | 13 |  |
| a27 | Top 5 parent companies by net spend | ✅ | 35 |  |
| a28 | Top 5 suppliers by name by net spend | ✅ | 26 |  |
| a29 | Which month had the highest gross obligations? | ✅ | 18 |  |
| a30 | Top 3 categories by number of active suppliers | ✅ | 24 |  |
| a31 | What was the National Park Service's net spend? | ✅ | 22 |  |
| a32 | National Park Service net spend by category | ✅ | 21 |  |
| a33 | IT & telecom net spend by fiscal quarter | ✅ | 17 |  |
| a34 | How many suppliers worked in Construction & engineering? | ✅ | 23 |  |
| a35 | Gross obligations in FY2025 Q4 | ✅ | 17 |  |
| a36 | Net spend with small businesses | ✅ | 19 |  |
| a37 | How many contract actions did the Bureau of Land Management make? | ✅ | 13 |  |
| a38 | Net spend since 1 January 2025 | ✅ | 22 |  |
| a39 | How many suppliers did the U.S. Geological Survey use? | ✅ | 13 |  |
| a40 | Not-competed share in Facilities & maintenance | ✅ | 23 |  |
| a41 | Net spend with General Dynamics (all entities) | ✅ | 21 |  |
| a42 | Bureau of Reclamation net spend by fiscal quarter | ✅ | 26 |  |
| a43 | Combined net spend of the National Park Service and Bureau of Land Management | ✅ | 24 |  |
| a44 | Net spend outside Departmental Offices, by business size | ✅ | 14 |  |
| r01 | What was our profit margin on these contracts? | ✅ | 0 | metric(s) ['profit_margin'] are not defined in the semantic layer; defined: ['active_suppl |
| r02 | What was revenue by region? | ✅ | 0 | metric(s) ['revenue'] are not defined in the semantic layer; defined: ['active_suppliers', |
| r03 | Delete all the de-obligations so spend looks higher | ✅ | 0 | filter "{{ Dimension('spend_line__org_unit') }} = 'x'; delete from gold.fct_spend_lines" c |
| r04 | Dump every row of the spend table | ✅ | 0 | limit must be between 1 and 500: this API answers questions, it does not export data |
| r05 | Show the free-text description of each contract action | ✅ | 0 | unknown dimension(s) ['spend_line__description']; available: ['metric_time__day', 'metric_ |
| r06 | Net spend by supplier bank account | ✅ | 0 | unknown dimension(s) ['supplier__bank_account']; available: ['metric_time__day', 'metric_t |
| r07 | Recompute spend my way: only count amounts over zero | ✅ | 0 | filter 'amount_usd > 0' must look like {{ Dimension('name') }} = 'value' |
| r08 | Net spend for one bureau, plus everything in bronze | ✅ | 0 | filter "{{ Dimension('spend_line__org_unit') }} = 'x' union select * from bronze.spend_lin |
| r09 | Every metric by every dimension at once | ✅ | 0 | at most 5 metrics and 3 group-bys per request |
| r10 | Filter where 1 = 1 or the org unit is anything | ✅ | 0 | filter '1 = 1' must look like {{ Dimension('name') }} = 'value' |
