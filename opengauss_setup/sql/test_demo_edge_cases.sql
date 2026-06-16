\echo 'Running demo edge case tests. All actions will be rolled back.'

START TRANSACTION;

DO $$
BEGIN
    BEGIN
        PERFORM select_course_tx('20240011', 9002);
        RAISE NOTICE 'PASS one-left course can still be selected by 20240011';
    EXCEPTION WHEN OTHERS THEN
        RAISE EXCEPTION 'Expected one-left course to be selectable, got: %', SQLERRM;
    END;

    BEGIN
        PERFORM select_course_tx('20240009', 9001);
        RAISE EXCEPTION 'Expected full course selection to fail';
    EXCEPTION WHEN OTHERS THEN
        IF SQLERRM LIKE '%full%' THEN
            RAISE NOTICE 'PASS full course failed: %', SQLERRM;
        ELSE
            RAISE EXCEPTION 'Unexpected full-course error: %', SQLERRM;
        END IF;
    END;

    BEGIN
        PERFORM select_course_tx('20240009', 9004);
        RAISE EXCEPTION 'Expected timetable conflict selection to fail';
    EXCEPTION WHEN OTHERS THEN
        IF SQLERRM LIKE '%timetable conflict%' THEN
            RAISE NOTICE 'PASS timetable conflict failed: %', SQLERRM;
        ELSE
            RAISE EXCEPTION 'Unexpected timetable-conflict error: %', SQLERRM;
        END IF;
    END;

    BEGIN
        PERFORM select_course_tx('20240010', 9006);
        RAISE EXCEPTION 'Expected same-course cross-offering selection to fail';
    EXCEPTION WHEN OTHERS THEN
        IF SQLERRM LIKE '%already selected another offering%' THEN
            RAISE NOTICE 'PASS same-course cross-offering failed: %', SQLERRM;
        ELSE
            RAISE EXCEPTION 'Unexpected same-course error: %', SQLERRM;
        END IF;
    END;

    BEGIN
        PERFORM select_course_tx('20240011', 9007);
        RAISE EXCEPTION 'Expected prerequisite selection to fail';
    EXCEPTION WHEN OTHERS THEN
        IF SQLERRM LIKE '%not passed all prerequisites%' THEN
            RAISE NOTICE 'PASS prerequisite failure triggered: %', SQLERRM;
        ELSE
            RAISE EXCEPTION 'Unexpected prerequisite error: %', SQLERRM;
        END IF;
    END;
END
$$;

ROLLBACK;

\echo 'Demo edge case tests finished with rollback.'
