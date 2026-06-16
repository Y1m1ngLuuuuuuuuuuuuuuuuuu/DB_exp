# Large Demo Dataset Validation Notes

The generator performs in-memory checks before writing SQL. Database-level validation is provided by `opengauss_setup/sql/validate_large_demo_dataset.sql`.

| Check | Generated State |
| --- | --- |
| Course offering capacity <= classroom capacity | `True` |
| Selected enrollment count <= max_capacity | `True` |
| Duplicate student/offering pairs avoided by generator | `True` |
| Current selected records avoid same-course cross-offering | `True` |
| Current selected records avoid timetable conflicts | `True` |
| Selected rows contain no final_score | `True` |
| Completed rows contain final_score | `True` |
| Score audit updates prepared | `80` |

## Executed Validation Result

`opengauss_setup/sql/validate_large_demo_dataset.sql` has been executed against the local `course-opengauss` container after importing `opengauss_setup/sql/local/seed_large_demo_dataset_20260611.sql`.

Key database-side results:

| Check | Result |
| --- | ---: |
| `student_count` | 100 |
| `teacher_count` | 30 |
| `course_count` | 50 |
| `offering_count` | 175 |
| `enrollment_count` | 1480 |
| `score_change_log_count` | 80 |
| Selected enrollment capacity violations | 0 |
| Classroom capacity violations | 0 |
| Duplicate student/offering violations | 0 |
| Same-course cross-offering selected violations | 0 |
| Selected timetable conflict violations | 0 |
| Prerequisite violations | 0 |
| Completed records without score | 0 |
| Selected records with score | 0 |
| Score out of range | 0 |
| Student role mismatch | 0 |
| Teacher role mismatch | 0 |
| Admin role mismatch | 0 |
| Self prerequisite | 0 |
| Prerequisite cycle | 0 |
| Invalid score log enrollment | 0 |
| Invalid score log user | 0 |

GPA view smoke checks returned 1480 `v_enrollment_grade_detail` rows and 284 `v_student_gpa_summary` rows.

## Edge-Case Fixture Validation

After applying `opengauss_setup/sql/seed_demo_edge_cases.sql`, the validation script was executed again. The database then contained 57 courses, 26 classrooms, 182 offerings, 221 schedule slots and 1495 enrollments. All integrity violation counts still returned `0`, including capacity, classroom capacity, duplicate selection, same-course cross-offering, timetable conflict, prerequisite, grade consistency, role consistency, prerequisite cycle and score audit log checks.

`opengauss_setup/sql/test_demo_edge_cases.sql` was also executed with rollback and confirmed:

- `EDGE_ONE_LEFT` can still be selected.
- `EDGE_FULL` fails because the offering is full.
- `EDGE_CONFLICT_B` fails for student `20240009` because of timetable conflict.
- Offering `9006` of `EDGE_SAME` fails for student `20240010` because of same-course cross-offering.
- `EDGE_ADV` fails for student `20240011` because the prerequisite `EDGE_PRE` has not been passed.
