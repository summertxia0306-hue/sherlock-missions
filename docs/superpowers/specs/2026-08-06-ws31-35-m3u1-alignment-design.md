# W01D31-W01D35 and S01D31-S01D35 M3U1 Alignment Design

Date: 2026-08-06

## Goal

Add five listening courses and five speaking courses as after-class consolidation
for 4A M3U1 `In our school`. The two tracks must stay on the same textbook page
and must not introduce M3U2 content.

The course sequence continues the current filename convention:

- Listening: `W01D31` through `W01D35`
- Speaking: `S01D31` through `S01D35`
- JSON metadata: `week = 4`, `day = 1..5`
- `open_date = 2026-08-06`, so all courses remain visible

The existing automatic recommendation logic remains unchanged. Listening keeps
recommending W01D30 while it is formally incomplete; speaking recommends S01D31
after the new courses are published.

## Source And Boundary

The verified source is the project copy of the 4A textbook, M3U1 printed pages
32-36. Mainline content must stay within these pages:

- school places: canteen, computer lab, office, gym, library, playground
- position: behind, in front of, on, in
- school description: `There is/are ...`
- school visit: building, floor, garden, cupboard, bookshelf, clean and tidy
- Animal School: forest, river, rabbit, `What's the matter?`, `I don't think
  so.`, `Come on!`, `Have a try!`
- school/classroom/schoolbag survey and `fr/gr/tr` sounds

M3U2 words and structures must not be introduced. In particular, supermarket,
post office, restaurant, street, next to, and between are out of scope.

## Shared Page Map

| Pair | Textbook page | Shared focus |
|---|---:|---|
| W01D31 / S01D31 | 32 | School places, behind/in front of, and the school rhyme |
| W01D32 / S01D32 | 33 | `There is/are ...`, classroom building, library, canteen, playground |
| W01D33 / S01D33 | 34 | A visit to Rainbow Primary School, floors, garden, clean and tidy |
| W01D34 / S01D34 | 35 | Animal School, feelings, ability, encouragement, and trying |
| W01D35 / S01D35 | 36 | `What's in ...?`, school/classroom/schoolbag review, and `fr/gr/tr` |

## Review Ratio

The parent selected plan A: about 80 percent M3U1 and 20 percent previously
learned review. Review may use `his/her`, `this/these`, `a/an`, `can + base
verb`, `likes + V-ing`, third-person singular, and question-response contrasts.
It must not become a route for teaching later-unit vocabulary.

Recent formal listening results support keeping L1 difficulty. W01D21-W01D29
were 90-100, with recent full scores; the observed misses were concentrated in
passage true/false and one question-response item. New courses therefore use
clear, age-appropriate distractors and retain focused practice in those sections
without raising sentence length sharply.

## Listening Structure

Each listening course has 20 questions and 100 total points:

1. `word_discrimination`: 4 questions
2. `sentence_meaning`: 4 questions
3. `question_response`: 4 questions
4. `dialogue`: 4 questions
5. `passage`: 4 questions using one shared passage audio

W01D31-W01D34 use `course_type = training`; W01D35 uses
`course_type = weekly_test`. Each course must have 18 MP3 files: `hello`,
`q01` through `q16`, and `p01`.

## Speaking Structure

Each speaking course has exactly eight questions: six `repeat` and two `qa`.
S01D31-S01D34 use `course_type = training`; S01D35 uses
`course_type = weekly_review`. Every speaking course must have eight MP3 files.

Text must stay short enough for a nine-year-old and should use textbook wording
or a minimal complete-sentence adaptation. The existing three-star gate,
third-attempt safety pass, first/last/best scores, per-take stars, weak words,
and `passed_by_safety` storage are unchanged.

## Deliverables

Add course JSON and audio under the existing content and static directories,
plus parent listening and speaking documents under `听力部分/Week4/`. Update
both audio manifests, README, module contracts, and the root learning archive.
The archive records course-material and operations status only; no new learning
conclusion or weak-word record is created from development or test activity.

No core application change is planned. Existing loading, ordering,
recommendation, recording, scoring, correction, and persistence logic should
accept the added JSON files unchanged.

## Verification And Deployment

Before deployment:

- add alignment tests for the five W/S pairs and forbidden M3U2 vocabulary;
- validate all listening and speaking JSON files;
- generate and verify 90 listening and 40 speaking MP3 files;
- run the complete regression suite, including data-kind and speaking gate;
- verify local list order, titles, entry, audio URLs, and parent views.

After pushing `main`, verify without submitting learner results:

- both lists show courses 01-35 in order;
- listening still recommends W01D30 if it remains formal-incomplete;
- speaking recommends S01D31;
- parent test remains isolated from formal completion;
- audio is reachable online.

Real iPad microphone permission, recording playback, and Xunfei scoring remain
parent-device checks.
