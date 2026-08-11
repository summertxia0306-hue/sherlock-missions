# W01D36-W01D40 and S01D36-S01D40 M3U2 Alignment Design

Date: 2026-08-11

## Goal

Add five listening courses and five speaking courses as after-class consolidation
for 4A M3U2 `Around my home`. The two tracks must stay on the same textbook page
and must not introduce M3U3 content.

The course sequence continues the existing filename convention:

- Listening: `W01D36` through `W01D40`
- Speaking: `S01D36` through `S01D40`
- JSON metadata: `week = 5`, `day = 1..5`
- `open_date = 2026-08-11`, so all five courses are visible after deployment

The automatic recommendation logic remains unchanged. The verified online
state on 2026-08-11 is that listening W01D35 is formally incomplete, so newly
published listening courses must not replace W01D35 as the recommendation.
Speaking S01D01-S01D35 are formally complete, so S01D36 becomes the first
recommended speaking course after publication.

## Source And Boundary

The verified source is the project copy of the 4A textbook, M3U2 printed pages
37-41. Mainline content must stay within these pages:

- places: supermarket, post office, restaurant, bakery, clothes shop, park,
  hotel, street, road, home, school
- position: near, behind, in front of, next to, between, in the centre of
- location and existence: `Where is ...?`, `Is/Are there ...?`,
  `Yes, there is/are.`, `No, there isn't/aren't.`
- street-corner conversation: `Excuse me.`, `Let me see.`, `We can show you
  the way.`, `It's our pleasure.`
- Nanjing Road reading: busy road, shops, restaurants, hotels, evening lights
- page 41 rhyme and `sl/sn/sw` sounds: slide, snake, swing

M3U3 shopping quantities and product packaging must not be introduced. In
particular, `a packet of`, `a loaf of`, `a bowl of`, `a bar of`, and
`a bottle of` are out of scope.

Textbook addresses such as `No. 126, Garden Street` are fictional practice
content. Speaking questions must not ask the learner to submit or record a real
home address.

## Selected Approach

The parent selected page-by-page alignment and a 90/10 content ratio:

- about 90 percent M3U2 textbook content;
- about 10 percent previously learned gap review embedded inside M3U2 contexts.

Review may cover `There is/are`, `this/these`, `a/an`, `can + base verb`,
third-person singular, and question forms. Review must not create unrelated
sentences or introduce vocabulary from a later unit.

No new formal wrong-answer or weak-word detail was read for this design. The
courses remain at L1 and must not be treated as evidence that the learner has
mastered M3U2.

## Shared Page Map

| Pair | Textbook page | Shared focus |
|---|---:|---|
| W01D36 / S01D36 | 37 | Home location, streets, nearby shops and parks, `Where is ...?`, `Is/Are there ...?` |
| W01D37 / S01D37 | 38 | Supermarket, post office, restaurant, `next to`, `between`, neighbourhood description |
| W01D38 / S01D38 | 39 | Street-corner dialogue, bakery, postcard, asking for places, showing the way, polite responses |
| W01D39 / S01D39 | 40 | Nanjing Road reading: centre, busy, shops, restaurants, hotels, evening lights |
| W01D40 / S01D40 | 41 and unit review | Location rhyme, `sl/sn/sw`, and a cumulative M3U2 weekly test/review |

Page 40 contains longer reading sentences. Listening may use the full ideas in
age-appropriate segments; speaking must use short complete sentences rather
than copying an entire long sentence into one repeat item.

## Listening Structure

Each listening course has 20 questions and 100 total points:

1. `word_discrimination`: 4 questions
2. `sentence_meaning`: 4 questions
3. `question_response`: 4 questions
4. `dialogue`: 4 questions
5. `passage`: 4 questions using one shared passage audio

W01D36-W01D39 use `course_type = training`; W01D40 uses
`course_type = weekly_test`. Each course must have 18 MP3 files: `hello`,
`q01` through `q16`, and `p01`.

Each course should contain about 18 M3U2-focused questions and about two
embedded review questions. Distractors must remain plausible for a nine-year-old
without relying on unlearned M3U3 vocabulary.

## Speaking Structure

Each speaking course has exactly eight questions: six `repeat` and two `qa`.
S01D36-S01D39 use `course_type = training`; S01D40 uses
`course_type = weekly_review`. Every speaking course must have eight MP3 files.

Across the batch, at least 36 of the 40 speaking items directly practise M3U2.
The remaining review items still use M3U2 place contexts. Existing three-star
gating, third-attempt safety pass, first/last/best scores, per-take stars,
`weak_words`, and `passed_by_safety` storage remain unchanged.

QA prompts use fixed textbook or fictional locations so the expected answer is
stable and no personal location data is requested.

## Deliverables

Add course JSON and audio under the existing content and static directories,
plus parent listening and speaking documents under `听力部分/Week5/`. Update
both audio manifests, README, both module contracts, and the root learning
archive with course-material and operations status only.

No core application change is planned. Existing loading, ordering,
recommendation, recording, scoring, correction, persistence, and test/formal
isolation logic should accept the added JSON files unchanged.

## Verification And Deployment

Before deployment:

- add alignment tests for all five W/S pairs and the M3U3 forbidden boundary;
- validate all listening and speaking JSON files;
- generate and decode-check 90 listening and 40 speaking MP3 files;
- verify every listening course has 18 MP3 files and every speaking course has 8;
- run the complete regression suite, including data-kind, access routes, and
  speaking gate tests;
- verify local list order, titles, entry, audio URLs, and parent views.

After pushing `main`, verify without submitting learner results:

- both lists show courses 01-40 in order;
- listening still recommends W01D35 while it remains formal-incomplete;
- speaking recommends S01D36;
- parent test remains isolated from formal completion;
- representative listening and speaking audio is reachable online.

Real iPad microphone permission, recording playback, and Xunfei scoring remain
parent-device checks. Development and parent test activity must not create
formal learning conclusions or update weak-word records.
