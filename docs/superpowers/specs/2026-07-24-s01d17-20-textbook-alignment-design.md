# S01D17-S01D20 Textbook Alignment Design

Date: 2026-07-24

## Goal

Keep the completed S01D16 course and its formal result unchanged. Rewrite only the
uncompleted S01D17-S01D20 courses so that they follow 4A M2U1 textbook pages
17-21 in order, then regenerate speaking audio and deploy without changing the
speaking gate, result schema, course IDs, or data-kind behavior.

## Course Map

| Course | Textbook source | Focus |
|---|---|---|
| S01D17 | pages 17-18, Look and say / Do a survey | `Do you have ...?`, `Yes, I do.`, `No, I don't.`, uncle/aunt/cousin quantities |
| S01D18 | page 19, Photos of Jill's family | cousin Wang Rong, age, `swim very fast`, uncle and `dive` |
| S01D19 | page 20, Mid-autumn Day | grandparents, mooncakes, garden, riddle, moon |
| S01D20 | page 21, Listen and enjoy / Learn the sound | cousin Bess, clothes descriptions, aunt/uncle, `Wash the fish.` |

Each course keeps six `repeat` questions and two `qa` questions. Sentences stay
short enough for a nine-year-old and use textbook wording or a minimal complete-
sentence adaptation needed by speech scoring.

## Compatibility

- Preserve IDs S01D17-S01D20 and all existing audio paths.
- Preserve `training` for S01D17-S01D19 and `weekly_review` for S01D20.
- Do not modify S01D16 or any formal result/recording.
- Do not modify the three-star gate, three-take safety pass, ISE scoring, or
  `formal`/`test` routing.
- Regenerate the 32 MP3 files and update the speaking manifest with the existing
  `tools/make_audio_speaking.py` workflow.

## Verification

- Add regression coverage for the exact textbook progression and removed
  synthetic phrases.
- Validate every speaking JSON file.
- Run the existing regression, data-kind, access-route, and speaking-gate tests.
- Verify eight non-empty MP3 files per optimized course and manifest coverage.
- Push to `main`, wait for Streamlit deployment, and verify S01D17-S01D20 titles,
  order, and question text through the authenticated parent view. Do not submit a
  test or formal course result during deployment verification.
