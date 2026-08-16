# W01D41-W01D50 and S01D41-S01D50 Review And Retention Design

Date: 2026-08-16

## Goal

Keep the existing Streamlit architecture and publish ten new paired listening
and speaking review courses. The new batch must remain within 4A M1U1 through
M3U2 and must not introduce M3U3.

The deployed course-material set becomes:

- Listening: `W01D39` through `W01D50`
- Speaking: `S01D39` through `S01D50`
- `W01D39`, `W01D40`, `S01D39`, and `S01D40` remain unchanged
- `W01D41-W01D50` and `S01D41-S01D50` are new cumulative review courses

Historical learning evidence remains independent from public course assets.
Deleting old JSON and MP3 files must not delete or rewrite private results,
wrong answers, corrections, speaking details, recordings, or Git history.

## Selected Architecture

The user selected the existing production architecture:

- Streamlit UI and routing remain in place.
- GitHub-backed private result and recording storage remains in place.
- Public course audio continues to use jsDelivr first and GitHub Raw fallback.
- The existing listening correction flow remains unchanged.
- The existing speaking three-star gate and third-attempt safety pass remain
  unchanged.
- Ordinary child entry remains `data_kind=formal`; authenticated parent test
  entry remains `data_kind=test`; test results never create child completion.

No Tencent Cloud migration or CloudBase rewrite is part of this change.

## Historical Asset Retention

Remove only reproducible public course material for `01-38`:

- `content/listening/W01D01.json` through `W01D38.json`
- `content/speaking/S01D01.json` through `S01D38.json`
- final public audio directories for `W01D01-W01D38`
- final public audio directories for `S01D01-S01D38`
- obsolete audio build fragments and their obsolete manifest entries

Keep all of the following:

- private formal and test result JSON
- listening `wrong_answers`, `section_scores`, and `corrections`
- speaking `question_results`, `weak_words`, `take_stars`, and
  `passed_by_safety`
- all private learner recordings and recording metadata
- historical parent reports and learning archive entries
- Git history, which remains the recovery path for removed public assets
- all public course material for `39-50`

The cleanup script must fail closed if a requested removal falls outside the
explicit `01-38` course ranges.

## Five-Course Student Window

The student course list no longer renders every retained course. It renders a
rolling window of at most five courses around the first formal-incomplete
course.

Algorithm:

1. Apply existing status and `open_date` visibility rules.
2. Find the first open course without a formal completion record. This remains
   the recommended course.
3. Show up to two immediately preceding courses, the recommended course, and
   up to two immediately following courses.
4. Near either end of the catalogue, fill the remaining slots from the other
   side so the window contains five courses when five are available.
5. If every retained course is formally complete, show the latest five and
   display the existing stage-complete message.

Examples for the retained `39-50` catalogue:

- recommended `39` -> show `39-43`
- recommended `40` -> show `39-43`
- recommended `44` -> show `42-46`
- all complete -> show `46-50`

This window applies to the normal child listening and speaking home pages.
Authenticated parent views continue to access every retained `39-50` course,
and direct links to retained courses continue to work. Removed `01-38` course
links return the existing not-found message while their historical result rows
remain readable in the parent record view.

## Paired Course Map

Listening and speaking remain on one shared track.

| Pair | Scope | Shared focus |
|---|---|---|
| W01D41 / S01D41 | M1U1 | introductions, name, age, student number, `my/your/his/her`, `This is ...` |
| W01D42 / S01D42 | M1U2 | ability verbs, `can + base verb`, `What can ... do?`, yes/no questions |
| W01D43 / S01D43 | M1U3 | feelings, `How do you feel?`, `Have some ...`, polite responses |
| W01D44 / S01D44 | M2U1 | family members, `have/has`, `Who is ...?`, age and ability |
| W01D45 / S01D45 | M2U2 | jobs, `What does ... do?`, `Is he/she ...?`, job locations |
| W01D46 / S01D46 | M2U3 | friends, clothes, appearance, `has/can/likes` |
| W01D47 / S01D47 | M3U1 | school places, `There is/are`, `behind/in front of`, school description |
| W01D48 / S01D48 | M3U2 | neighbourhood places, `next to/between`, location and existence questions |
| W01D49 / S01D49 | M1-M2 review | people, family, jobs, feelings, abilities, and recurring old gaps |
| W01D50 / S01D50 | M1-M3U2 review | school, neighbourhood, people, abilities, and full cumulative review |

Recurring review may include `his/her`, `my/your`, `a/an`, `this/these`,
`can + base verb`, `like + V-ing`, third-person `has/lives/walks/likes`,
question marks and general questions, `foot/leg`, `bitter/butter`, and
`present`. M3U3 quantity and shopping expressions remain forbidden.

## Listening Structure

Every new listening course has 20 questions and 100 points:

1. `word_discrimination`: 4
2. `sentence_meaning`: 4
3. `question_response`: 4
4. `dialogue`: 4
5. `passage`: 4 using one shared passage audio

`W01D41-W01D48` use `course_type=training`. `W01D49-W01D50` use
`course_type=weekly_test`. Each course has 18 final MP3 files: `hello`,
`q01-q16`, and `p01`.

## Speaking Structure

Every new speaking course has exactly eight questions: six `repeat` and two
`qa`. `S01D41-S01D48` use `course_type=training`; `S01D49-S01D50` use
`course_type=weekly_review`. Each course has eight final MP3 files.

Sentences remain short enough for a nine-year-old. QA prompts use a fixed
Chinese answer hint and a unique expected English answer. Existing first,
last, best, per-take stars, weak words, and safety-pass persistence remain
unchanged.

## Documentation And Archive

Update README and both module contracts to replace the old all-visible rule
with the rolling student window and to record the active `39-50` material set.
Update the root learning archive only with course-material and operations
status. Do not create learning conclusions from development or parent tests.

Parent documents must provide the listening transcripts/answers and speaking
texts/expected answers for `41-50`. Historical reports remain untouched.

## Verification

Before deployment:

- add unit tests for the five-course window at the beginning, middle, end, and
  all-complete states;
- verify recommendation still uses formal completion only;
- verify parent test can access all retained `39-50` courses;
- verify removed course results remain readable without loading removed JSON;
- validate every retained and new listening/speaking JSON;
- verify `39-40` files are byte-identical before and after the change;
- generate 180 new listening MP3 files and 80 new speaking MP3 files;
- verify final audio counts: 18 per listening course and 8 per speaking course;
- verify manifests contain only retained/new course entries and live fragments;
- run the complete test suite, including regression, data-kind, access-route,
  recommendation, course-alignment, and speaking-gate tests.

After pushing `main`, verify without creating formal learner data:

- student lists render only the correct five-course windows;
- `W01D39` and `S01D39` remain recommended while formally incomplete;
- `39-40` enter and play normally;
- representative `41-50` audio resolves through CDN and Raw fallback;
- authenticated test submissions remain test-only;
- ordinary child entry remains formal;
- speaking recording, replay, scoring, and the third-attempt safety pass remain
  operational.

Real iPad microphone permission and recording acceptance remain parent-device
checks. No development result may be used as formal learning evidence.
