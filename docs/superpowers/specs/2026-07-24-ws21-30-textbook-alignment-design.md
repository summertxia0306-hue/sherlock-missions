# W01D21-W01D30 and S01D21-S01D30 Textbook Alignment Design

Date: 2026-07-24

## Goal

Add ten listening courses and ten speaking courses while bringing both tracks
back onto one textbook timeline. Each listening/speaking pair must use the same
4A textbook page, and a speaking course must not introduce vocabulary from a
later page.

The new courses continue the existing filename sequence because the current
loader sorts JSON filenames and has no automatic W02/S02 week rollover:

- Listening: `W01D21` through `W01D30`
- Speaking: `S01D21` through `S01D30`
- JSON metadata: `week = 3`, `day = 1..10`
- `open_date = 2026-07-24`, so all courses remain visible

The recommendation logic remains unchanged. It continues to select the first
visible course without a formal completion, so later courses cannot cover an
earlier incomplete course.

## Source Of Truth

All new mainline content comes from the verified 4A textbook PDF and lesson
index:

- M2U2 Jobs: textbook pages 22-26
- M2U3 I have a friend: textbook pages 27-31

Old-error review may use vocabulary and structures already encountered in
earlier courses, but it must not be used to introduce vocabulary from a later
textbook page.

## Shared Page Map

| Pair | Textbook page | Shared focus |
|---|---:|---|
| W01D21 / S01D21 | 22 | Fire rhyme: fire, fire station, 119, fire engine, firefighters, put out the fire |
| W01D22 / S01D22 | 23 | Jobs and `What does your father/mother do?` / `He/She is ...` |
| W01D23 / S01D23 | 24 | Job guessing: `Is he/she ...?`, `Yes, ... is.`, `No, ... isn't.` |
| W01D24 / S01D24 | 25 | Visiting a fire station: dangerous, afraid, help people, like my job, You're welcome |
| W01D25 / S01D25 | 26 | Family-job survey, M2U2 review, and `dr/pr`: dress, princess, dream, pretty |
| W01D26 / S01D26 | 27 | Friend descriptions: name, build, clothes, and abilities |
| W01D27 / S01D27 | 28 | Clothes and colours with `He/She has ...` |
| W01D28 / S01D28 | 29 | The lion and the mouse: strong, teeth, sharp, net, afraid, bite, help, friends |
| W01D29 / S01D29 | 30 | Short shorts rhyme: wearing, long jackets, T-shirts, socks, short shorts |
| W01D30 / S01D30 | 31 | Friend profile, M2U3 review, and `br/cr`: bread, ice cream |

## Listening Courses

Each listening course keeps the established 20-question, 100-point structure:

1. `word_discrimination`: 4 questions
2. `sentence_meaning`: 4 questions
3. `question_response`: 4 questions
4. `dialogue`: 4 questions
5. `passage`: 4 questions using one shared passage audio

`W01D25` and `W01D30` use `course_type = weekly_test`; other courses use
`training`. Every course must have 18 MP3 files: `hello`, `q01` through `q16`,
and `p01`.

The child's accumulated listening results show that question response and word
discrimination remain the relatively weaker sections. New courses keep the
same L1 difficulty but use close, age-appropriate distractors in those two
sections. Difficulty must not be raised merely because W01D20 was completed.

### Listening Review Boundaries

- Daily courses use the assigned page as the main content and may devote a
  small minority of questions to previously learned material.
- W01D25 reviews pages 22-26 and may lightly revisit M2U1 family language.
- W01D30 reviews pages 27-31 and may lightly revisit M2U2 jobs.
- Historical review targets include `a/an`, `his/her`, `this/these`,
  `can + base verb`, `like + V-ing`, `has`, question marks, `tooth/teeth`,
  `foot/leg`, and `bitter/butter`.
- No review question may introduce a word from a later page in the new unit.

## Speaking Courses

Each speaking course keeps exactly eight questions:

- Six `repeat` questions
- Two `qa` questions with a unique Chinese hint and expected answer

The existing three-star gate remains unchanged: retry below three stars; after
the third scored attempt below three stars, show the safety-pass action. Keep
first, last, best, per-take stars, weak words, and `passed_by_safety`.

Speaking targets should use textbook wording or a minimal complete-sentence
adaptation required by speech scoring. Long rhyme or story lines must be split
into short, child-sized utterances. In particular:

- S01D21 treats `brave` and `put out` as rhyme comprehension, not independent
  productive vocabulary.
- S01D24 introduces `dangerous` and `afraid` only when page 25 is reached.
- S01D28 introduces `sharp`, `bite`, and `net` only when page 29 is reached.
- S01D29 splits the page 30 rhyme rather than scoring a full stanza at once.
- S01D30 splits the friend profile into short sentences and uses short `br/cr`
  sound lines rather than one long paragraph.

`S01D25` and `S01D30` use `course_type = weekly_review`; other courses use
`training`. Every speaking course must have eight MP3 files.

## Files And Documentation

Add:

- `content/listening/W01D21.json` through `W01D30.json`
- `content/speaking/S01D21.json` through `S01D30.json`
- `static/audio/listening/W01D21/` through `W01D30/`
- `static/audio/speaking/S01D21/` through `S01D30/`
- Parent listening and speaking documents under `听力部分/Week3/`

Update both audio manifests, `README.md`, both module contracts, and the root
learning archive. The archive records only course-material and operations
status; it must not add learning conclusions, L numbers, or speaking weak words
without new formal evidence.

No core application change is planned. Existing course loading, sorting,
recommendation, recording, scoring, correction, and result persistence should
accept the new JSON files without modification.

## Verification And Deployment

Before deployment:

- Add content-alignment regression tests that lock every W/S pair to its source
  page and prevent later-page vocabulary from leaking forward.
- Validate every listening and speaking JSON file.
- Run the complete existing test suite, including data-kind, access routes,
  recommendation, listening regressions, speaking gate, and S17-S20 alignment.
- Generate audio only with the existing tools and verify expected counts,
  non-empty files, manifest text, and local/CDN/Raw hashes.
- Start the local app and check list order, course entry, and visible titles.

After pushing `main`, verify online without submitting a result:

- Listening and speaking lists show courses 01-30 in order.
- Listening recommends W01D21 if W01D01-W01D20 remain formally complete.
- Speaking continues to recommend the earliest formal-incomplete course; an
  incomplete S01D17-S01D20 must not be covered by S01D21.
- Parent text/answer views show the page-aligned content.
- Existing test/formal boundaries and speaking gate remain intact.

The parent iPad remains the final authority for real audio playback, microphone
permission, recording playback, and Xunfei scoring.
