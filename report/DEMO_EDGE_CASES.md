# Demo Edge Cases

This document lists deterministic edge-case courses for frontend and database-rule testing. The data is inserted by:

```bash
docker exec -i course-opengauss bash -lc 'export GAUSSHOME=/usr/local/opengauss; export PATH="$GAUSSHOME/bin:$PATH"; export LD_LIBRARY_PATH="$GAUSSHOME/lib:${LD_LIBRARY_PATH:-}"; gsql -v ON_ERROR_STOP=1 -U gaussdb -W Secretpassword@123 -d course_system -p 5432' < opengauss_setup/sql/seed_demo_edge_cases.sql
```

The rollback test is:

```bash
docker exec -i course-opengauss bash -lc 'export GAUSSHOME=/usr/local/opengauss; export PATH="$GAUSSHOME/bin:$PATH"; export LD_LIBRARY_PATH="$GAUSSHOME/lib:${LD_LIBRARY_PATH:-}"; gsql -v ON_ERROR_STOP=1 -U gaussdb -W Secretpassword@123 -d course_system -p 5432' < opengauss_setup/sql/test_demo_edge_cases.sql
```

## Edge Course Matrix

| Scenario | Course | Offering | Current State | Test Account | Expected Result |
| --- | --- | ---: | --- | --- | --- |
| Full course | `EDGE_FULL` 演示：已满课程 | `9001` | `8 / 8`, remaining `0` | `20240009` | Selection fails: course offering is full |
| One seat left | `EDGE_ONE_LEFT` 演示：仅剩一名课程 | `9002` | `5 / 6`, remaining `1` | `20240011` | Selection succeeds, then remaining capacity becomes `0` |
| Timetable conflict | `EDGE_CONFLICT_A` / `EDGE_CONFLICT_B` | `9003` / `9004` | `20240009` already selected `9003`; both meet 周六 1-2 节 | `20240009` selects `9004` | Selection fails: timetable conflict |
| Same course across offerings | `EDGE_SAME` | `9005` / `9006` | `20240010` already selected offering `9005` | `20240010` selects `9006` | Selection fails: same course in same semester |
| Missing prerequisite | `EDGE_ADV` requires `EDGE_PRE` | `9007` | Student has not passed `EDGE_PRE` | `20240011` | Selection fails: prerequisites not passed |

## Current Database Verification

After applying the edge-case seed, `v_course_offering_detail` reports:

| course_id | offering_id | selected_count | max_capacity | remaining_capacity |
| --- | ---: | ---: | ---: | ---: |
| `EDGE_FULL` | `9001` | 8 | 8 | 0 |
| `EDGE_ONE_LEFT` | `9002` | 5 | 6 | 1 |
| `EDGE_CONFLICT_A` | `9003` | 1 | 20 | 19 |
| `EDGE_CONFLICT_B` | `9004` | 0 | 20 | 20 |
| `EDGE_SAME` | `9005` | 1 | 20 | 19 |
| `EDGE_SAME` | `9006` | 0 | 20 | 20 |
| `EDGE_ADV` | `9007` | 0 | 20 | 20 |

`test_demo_edge_cases.sql` passed with rollback:

```text
PASS one-left course can still be selected by 20240011
PASS full course failed: Course offering 9001 is full
PASS timetable conflict failed: Student 20240009 has a timetable conflict for offering 9004
PASS same-course cross-offering failed: Student 20240010 has already selected another offering for course EDGE_SAME in semester 2025-2026-2
PASS prerequisite failure triggered: Student 20240011 has not passed all prerequisites for course EDGE_ADV
```

`validate_large_demo_dataset.sql` still reports zero violations after the edge cases are inserted.
