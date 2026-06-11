# Large Demo Dataset Summary

- Random seed: `20260611`
- Departments: `4`
- Majors: `11`
- Students: `100`
- Teachers: `30`
- Administrators: `3`
- Courses: `50`
- Semesters: `4`
- Classrooms: `20`
- Course offerings: `175`
- Schedule slots: `214`
- Enrollments: `1480`
- Completed enrollments: `1000`
- Selected enrollments: `425`
- Dropped enrollments: `55`
- Score audit updates generated through trigger: `80`

## Department Distribution

| department | students | teachers | courses |
| --- | ---: | ---: | ---: |
| 计算机学院 | 25 | 9 | 15 |
| 数学与统计学院 | 25 | 7 | 10 |
| 外国语学院 | 25 | 6 | 10 |
| 经济管理学院 | 25 | 8 | 15 |

## Course Type Distribution

| course_type | count |
| --- | ---: |
| elective | 18 |
| public | 12 |
| required | 20 |

## Score Distribution

| score band | count |
| --- | ---: |
| 90-100 | 242 |
| 80-89 | 340 |
| 70-79 | 291 |
| 60-69 | 108 |
| 0-59 | 19 |

## Semester Distribution

| semester | offerings | enrollments |
| --- | ---: | ---: |
| 2024-2025-1 | 30 | 559 |
| 2024-2025-2 | 40 | 312 |
| 2025-2026-1 | 45 | 129 |
| 2025-2026-2 | 60 | 480 |

## Recommended Demo Accounts

- Administrator: `A001`
- Teachers: `T005`, `T021`
- Students: `20240004`, `20240008`, `20240012`

Plaintext passwords are stored only in `secrets/DEMO_ACCOUNT_CREDENTIALS.md`.

## Optional Edge-Case Fixtures

`opengauss_setup/sql/seed_demo_edge_cases.sql` adds deterministic test courses for frontend and trigger demonstrations. After applying it, the local database contains:

- Courses: `57`
- Classrooms: `26`
- Course offerings: `182`
- Schedule slots: `221`
- Enrollments: `1495`
- Score change logs: `80`

Edge courses:

| scenario | course_id | offering_id | selected / capacity | test account |
| --- | --- | ---: | --- | --- |
| full course | `EDGE_FULL` | 9001 | `8 / 8` | `20240009` |
| one seat left | `EDGE_ONE_LEFT` | 9002 | `5 / 6` | `20240011` |
| timetable conflict | `EDGE_CONFLICT_A` / `EDGE_CONFLICT_B` | 9003 / 9004 | `1 / 20`, `0 / 20` | `20240009` |
| same-course cross-offering | `EDGE_SAME` | 9005 / 9006 | `1 / 20`, `0 / 20` | `20240010` |
| missing prerequisite | `EDGE_ADV` requires `EDGE_PRE` | 9007 | `0 / 20` | `20240011` |

See `report/DEMO_EDGE_CASES.md` for expected test outcomes.
