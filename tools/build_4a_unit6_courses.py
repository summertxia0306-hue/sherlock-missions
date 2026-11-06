# -*- coding: utf-8 -*-
"""Build Unit 6 D36–D40 from original exercises grounded in B008."""
from pathlib import Path
from random import Random

from build_4a_starter_courses import (
    a, c, word, sentence, response, dialogue, passage_statement, parent_note,
    json_write, child_listening, child_speaking, answer_text, transcript_text,
)
from build_4a_unit2_courses import SECTION_SPECS, make_section, child_catalog_entry
from build_4a_unit1_unit2_review_courses import audio_plan

ROOT = Path(__file__).resolve().parents[1]
DRAFT = ROOT / "content/drafts/4A-T1-W01-UNIT6"
PREFIX = ROOT / "docs/course-batches/2026-11-06-4A-Unit6-D36-D40"
META = {
    36: ("秋日农场", "p47-p49", "L1", 12, 10, [2, 2, 2, 2, 3]),
    37: ("秋游观察", "p47-p50", "L1", 14, 10, [2, 2, 2, 2, 3]),
    38: ("秋景感叹句", "p47-p51", "L2", 17, 12, [2, 2, 2, 2, 3]),
    39: ("塞罕坝故事", "p47-p53", "L2", 21, 12, [1, 2, 2, 2, 3]),
    40: ("秋天小诗与综合", "p47-p54", "L3", 25, 12, [1, 1, 2, 2, 3]),
}

# Listening clips and choices are authored for this batch. They do not
# reconstruct answers to missing recordings or photo-only textbook items.
DATA = {
    36: {
        "words": [("farm", "farm|fruit|fall", 0), ("leaf", "apple|leaf|field", 1), ("fly south", "pick fruits|fall down|fly south", 2), ("sweet fruits", "sweet fruits|colourful leaves|beautiful fields", 0)],
        "sentences": [
            ("I love autumn days.", "I love autumn days.", True),
            ("The leaves are on the trees.", "The leaves are falling.", False),
            ("My parents work in our fields.", "My parents work in our fields.", True),
            ("Birds fly north.", "Birds fly south.", False),
        ],
        "responses": [
            ("Where do your parents work?", "In our fields.|I love autumn.|They are sweet.", 0),
            ("What do the little animals collect?", "Apples are sweet.|They collect food.|They fly south.", 1),
            ("Do you like autumn days?", "They are in the fields.|I pick fruits.|Yes, I do.", 2),
            ("What are the fruits like?", "They are sweet.|They work in the fields.|They fly south.", 0),
        ],
        "dialogues": [
            (["I love autumn days on the farm.", "What do you pick there?", "I pick sweet apples."], "What does the child pick?", "Apples.|Leaves.|Flowers.", 0),
            (["Look at the birds.", "Are they flying south?", "Yes, they are."], "Which way are the birds flying?", "North.|South.|Across the field only.", 1),
            (["I like looking for colourful leaves.", "I like taking photos of the fields."], "What does the second child like doing?", "Picking fruits.|Watching birds.|Taking photos.", 2),
            (["Do your parents work in the fields?", "Yes, they do. I pick fruits with my friends."], "Who works in the fields?", "The child's parents.|The child's friends.|The little animals.", 0),
        ],
        "passage": "I am a farm boy. I love autumn days. My friends and I dance with falling leaves and pick sweet fruits. My parents work in the fields. Birds fly south. Little animals collect food.",
        "statements": [("The boy loves autumn days.", True), ("The friends pick sweet fruits.", True), ("The boy's parents work in a shop.", False), ("The little animals do not collect food.", False)],
        "repeat": ["I am a happy farm boy.", "I love autumn days.", "We dance with falling leaves.", "We pick nice and sweet fruits.", "My parents work in our fields.", "Birds fly south."],
        "qa": [
            ("What do the children pick on the farm?", "They pick sweet fruits.", "他们采摘甜甜的水果。"),
            ("Where do the farm boy's parents work?", "They work in the fields.", "他们在田里工作。"),
            ("Which way do the birds fly?", "They fly south.", "它们向南飞。"),
            ("What do the little animals collect?", "They collect food.", "它们收集食物。"),
        ],
    },
    37: {
        "words": [("an autumn outing", "a farm boy|an autumn outing|an autumn day", 1), ("a falling leaf", "a blue sky|a high kite|a falling leaf", 2), ("take a photo", "take a photo|pick an apple|look for leaves", 0), ("across the sky", "in the fields|across the sky|on the farm", 1)],
        "sentences": [
            ("Miss Li and her students go on an autumn outing.", "Miss Li and her students go on an autumn outing.", True),
            ("A falling Wutong leaf tells us spring is coming.", "A falling Wutong leaf tells us autumn is coming.", False),
            ("The kites are low.", "The kites are high.", False),
            ("Some birds are flying across the sky.", "Some birds are flying across the sky.", True),
        ],
        "responses": [
            ("What are the birds doing?", "The sky is blue.|They are flying.|They are kites.", 1),
            ("What tells us that autumn is coming?", "They are getting closer.|A falling Wutong leaf.|The kite is high.", 1),
            ("What colour is the sky?", "They are colourful.|It is high.|It is blue.", 2),
            ("Shall we take a photo?", "Yes, let's do that.|They are leaves.|The sky is high.", 0),
        ],
        "dialogues": [
            (["Look at these Wutong trees.", "A leaf is falling. Autumn is coming."], "What is falling?", "An apple.|A leaf.|A kite.", 1),
            (["The sky is blue. Look at the kites!", "They are very high."], "What is high in the sky?", "The trees.|The leaves.|The kites.", 2),
            (["Some birds are flying across the sky.", "They are getting closer. Let's take a photo."], "What do the children want to do?", "Take a photo.|Pick fruits.|Fly a kite.", 0),
            (["Boys and girls, please go and find autumn.", "Look! These Wutong leaves are beautiful.", "Well done. You found lovely autumn."], "What do the students notice?", "Golden apples.|Beautiful Wutong leaves.|Little animals.", 1),
        ],
        "passage": "Miss Li takes her students on an autumn outing. They look at the beautiful Wutong leaves. One leaf is falling. They see a blue sky and high kites. Some birds fly across the sky and get closer. The students want to take a photo.",
        "statements": [("The students go on an autumn outing.", True), ("A Wutong leaf is falling.", True), ("The sky is grey.", False), ("The birds are getting farther away.", False)],
        "repeat": ["We go on an autumn outing.", "A Wutong leaf is falling.", "How beautiful these Wutong leaves are!", "How blue the sky is!", "How high the kites are!", "Some birds are flying across the sky."],
        "qa": [
            ("What do the students see in the trees?", "They see beautiful Wutong leaves.", "他们看到漂亮的梧桐叶。"),
            ("What is falling from a Wutong tree?", "A leaf is falling.", "一片叶子正在落下。"),
            ("What are the birds doing?", "They are flying across the sky.", "它们正飞过天空。"),
            ("What do the students want to take?", "They want to take a photo.", "他们想拍一张照片。"),
        ],
    },
    38: {
        "words": [("blue sky", "blue sky|high kites|sweet fruits", 0), ("busy farmer", "happy farm boy|busy farmer|little animal", 1), ("beautiful leaves", "falling fruits|beautiful fields|beautiful leaves", 2), ("high kites", "high kites|tall trees|blue sky", 0)],
        "sentences": [
            ("How blue the sky is!", "How blue the sky is!", True),
            ("How high the kites are!", "How beautiful the leaves are!", False),
            ("How busy the farmer is!", "How busy the farmer is!", True),
            ("The leaves are falling.", "The birds are flying.", False),
        ],
        "responses": [
            ("The sky looks very blue. What can you say?", "How blue the sky is!|How high the kites are!|How busy the farmer is!", 0),
            ("Look at those beautiful leaves. What can you say?", "How beautiful the leaves is!|How beautiful the leaves are!|How beautiful is the leaves!", 1),
            ("The farmer is very busy. What can you say?", "How busy the farmer are!|How busy are the farmer!|How busy the farmer is!", 2),
            ("Look at those high kites. What can you say?", "How high the kites are!|How high the kites is!|How blue the sky is!", 0),
        ],
        "dialogues": [
            (["Look up. How blue the sky is!", "Let's take a photo of it."], "What do they want to photograph?", "The blue sky.|The sweet fruits.|The falling leaves.", 0),
            (["How busy the farmer is!", "Yes. He is picking fruits on the farm."], "Who is picking fruits?", "The farm boy.|The farmer.|The students.", 1),
            (["How high the kites are!", "Yes, but those birds are flying even higher."], "What is flying higher than the kites?", "Leaves.|Apples.|Birds.", 2),
            (["How beautiful the leaves are!", "Look! Some are falling. Let's watch them."], "What do they want to watch?", "The falling leaves.|The busy farmer.|The high kites.", 0),
        ],
        "passage": "It is a cool autumn day. Two friends are on an outing. One friend takes a photo of the blue sky. The other looks at the beautiful falling leaves. The boys fly kites. The friends see a busy farmer picking fruits.",
        "statements": [("The friends are on an autumn outing.", True), ("One friend takes a photo of the blue sky.", True), ("The boys pick fruits in this passage.", False), ("The farmer is flying a kite.", False)],
        "repeat": ["How blue the sky is!", "How high the kites are!", "How busy the farmer is!", "How beautiful the leaves are!", "Colourful leaves fall.", "We take photos of the blue sky."],
        "qa": [
            ("What can you say about the blue sky? Start with How.", "How blue the sky is!", "用 How 感叹：天空多蓝啊！"),
            ("What can you say about the high kites? Start with How.", "How high the kites are!", "用 How 感叹：风筝多高啊！"),
            ("What can you say about the busy farmer?", "How busy the farmer is!", "用 How 感叹：这位农民多忙啊！"),
            ("What can you say about the beautiful leaves?", "How beautiful the leaves are!", "用 How 感叹：这些叶子多美啊！"),
            ("What do the boys fly on the outing?", "They fly kites.", "他们放风筝。"),
            ("What do the friends take photos of?", "They take photos of the blue sky.", "他们给蓝蓝的天空拍照。"),
        ],
    },
    39: {
        "words": [("colourful forest", "colourful forest|golden fields|tall tree", 0), ("golden fields", "blue sky|golden fields|sweet apples", 1), ("pick apples", "pick up leaves|watch birds|pick apples", 2), ("working hard", "working hard|flying south|taking photos", 0), ("a tall tree", "a high kite|a tall tree|a busy worker", 1)],
        "sentences": [
            ("Minmin visits the park with his family.", "Minmin visits the park with his family.", True),
            ("Minmin sees golden fields.", "Minmin sees golden fields.", True),
            ("Grandpa shows Minmin two tall trees.", "Grandpa shows Minmin one tall tree.", False),
            ("The workers are working hard.", "The workers are working hard.", True),
            ("Minmin enjoys picking leaves.", "Minmin enjoys picking apples.", False),
        ],
        "responses": [
            ("What does Minmin enjoy picking in the park?", "He enjoys picking apples.|He enjoys flying kites.|He enjoys taking photos.", 0),
            ("What does Grandpa show Minmin?", "He shows him a photo.|He shows him a tall tree.|He shows him some kites.", 1),
            ("How does Minmin feel about the forest and fields?", "He is tired.|He is sad.|He is excited.", 2),
            ("What are the workers doing?", "They are working hard.|They are flying south.|They are falling.", 0),
            ("What can you say about the beautiful autumn there?", "How busy the farmer is!|How beautiful autumn is here!|How high the kites are!", 1),
        ],
        "dialogues": [
            (["Minmin is excited to see the colourful forest.", "He can see golden fields too."], "Which two things make Minmin excited?", "The forest and fields.|The shop and farm.|The birds and kites.", 0),
            (["Do you enjoy picking apples here, Minmin?", "Yes. I enjoy watching birds too."], "What else does Minmin enjoy?", "Taking photos.|Watching birds.|Flying kites.", 1),
            (["There are many trees here now.", "Years ago, people could see only one tree here.", "Grandpa, please show me that tree."], "What does the first speaker notice about the place now?", "There is no tree.|There is only one tree.|There are many trees.", 2),
            (["Look at those workers, Minmin. They are working hard.", "Many people like them make this place wonderful."], "Who helps make the place wonderful?", "The workers and people like them.|The birds and little animals.|Minmin and his classmates.", 0),
            (["Grandpa, how beautiful autumn is here!", "Yes. Look at that tall tree."], "What does Grandpa ask Minmin to look at?", "A golden field.|A tall tree.|A bird in the sky.", 1),
        ],
        "passage": "Minmin and his family visit Saihanba National Forest Park. He is excited to see the colourful forest and the golden fields. He enjoys picking apples and watching birds. Grandpa shows him a tall tree. Grandpa says that years ago people could see only one tree there. He tells Minmin that many people work hard to make this place wonderful.",
        "statements": [("Minmin goes to Saihanba with his family.", True), ("He sees a colourful forest.", True), ("He enjoys picking apples and flying kites.", False), ("Grandpa says there were many trees there years ago.", False), ("Grandpa talks about people who work hard.", True)],
        "repeat": ["Minmin sees a colourful forest.", "He is excited to see the golden fields.", "He enjoys picking apples and watching birds.", "Grandpa shows him a tall tree.", "The workers are working hard.", "How beautiful autumn is here!"],
        "qa": [
            ("What colour are the fields Minmin sees?", "The fields are golden.", "田野是金色的。"),
            ("What two things does Minmin enjoy doing?", "He enjoys picking apples and watching birds.", "他喜欢摘苹果和看鸟。"),
            ("What does Grandpa show Minmin?", "Grandpa shows him a tall tree.", "爷爷给他看一棵高大的树。"),
            ("How many trees does Grandpa say people could see there years ago?", "They could see only one tree.", "他们只看得到一棵树。"),
            ("What are the workers doing?", "They are working hard.", "他们正在努力工作。"),
            ("What can Minmin say about autumn there?", "How beautiful autumn is here!", "用 How 感叹：这里的秋天多美啊！"),
        ],
    },
    40: {
        "words": [("feel the cool wind", "feel the cool wind|smell nice fruits|see golden fields", 0), ("pick up leaves", "pick apples|pick up leaves|watch birds", 1), ("smell nice fruits", "see colourful trees|feel the cool wind|smell nice fruits", 2), ("birds flying south", "birds flying south|workers picking apples|boys flying kites", 0), ("lovely autumn", "busy farmer|lovely autumn|beautiful leaves", 1)],
        "sentences": [
            ("I see birds flying south.", "I see birds flying south.", True),
            ("I feel the warm wind.", "I feel the cool wind.", False),
            ("I smell nice fruits.", "I smell nice fruits.", True),
            ("I pick up colourful leaves.", "I pick up colourful leaves.", True),
            ("How busy the farmer is!", "How lovely autumn is!", False),
        ],
        "responses": [
            ("What do you feel in the autumn poem?", "I feel the cool wind.|I see the cool wind.|I smell the cool wind.", 0),
            ("What do you smell in the poem?", "I smell colourful leaves.|I smell nice fruits.|I smell the blue sky.", 1),
            ("What do you pick up in the poem?", "I pick up some kites.|I pick up some birds.|I pick up colourful leaves.", 2),
            ("The leaves are beautiful. What can you say?", "How beautiful the leaves are!|How beautiful the leaves is!|How beautiful are the leaves!", 0),
            ("What does Minmin enjoy doing in Saihanba?", "He enjoys flying kites.|He enjoys picking apples.|He enjoys working in the fields.", 1),
        ],
        "dialogues": [
            (["I can feel the cool wind.", "I can smell nice fruits."], "What does the second speaker smell?", "Nice fruits.|Colourful leaves.|The cool wind.", 0),
            (["I see birds flying south.", "Look down. There are colourful leaves on the ground.", "Let's pick some up."], "What are they going to pick up?", "Apples.|Leaves.|Kites.", 1),
            (["Look at that tall tree in Saihanba.", "Grandpa says many people work hard to make the park wonderful."], "Who helps make the park wonderful?", "The students on the outing.|The birds flying south.|The people who work hard there.", 2),
            (["The sky is blue and the kites are high.", "I want a photo of the kites, not the leaves."], "What does the second speaker want to photograph?", "The kites.|The leaves.|The apples.", 0),
            (["Can you read a line from your autumn poem?", "Yes. I feel the cool wind."], "What does the line describe?", "Smelling fruit.|Feeling the wind.|Seeing leaves.", 1),
        ],
        "passage": "It is autumn. I see birds flying south and feel the cool wind. On the farm, I smell nice fruits. My friend picks up colourful leaves. We look up and see high kites in the blue sky. We take a photo of the kites. Back at school, we share a poem about what we see, smell, feel and do in autumn.",
        "statements": [("The speaker sees birds flying south.", True), ("The speaker feels a warm wind.", False), ("The speaker's friend picks up colourful leaves.", True), ("They take a photo of the kites.", True), ("At school they share a poem about winter.", False)],
        "repeat": ["It is autumn.", "I see birds flying south.", "I smell nice fruits.", "I pick up colourful leaves.", "I feel the cool wind.", "How lovely autumn is!"],
        "qa": [
            ("What do you see in the poem?", "I see birds flying south.", "我看到鸟儿向南飞。"),
            ("What do you smell in the poem?", "I smell nice fruits.", "我闻到水果的香味。"),
            ("What do you pick up in the poem?", "I pick up colourful leaves.", "我捡起五颜六色的树叶。"),
            ("What do you feel in the poem?", "I feel the cool wind.", "我感觉到凉爽的风。"),
            ("What can you say at the end of the poem?", "How lovely autumn is!", "用 How 感叹：秋天多可爱啊！"),
            ("What can you say about the blue sky and high kites?", "How blue the sky is! How high the kites are!", "用两个 How 感叹句：天空多蓝啊！风筝多高啊！"),
        ],
    },
}


def build(day):
    title, pages, difficulty, lmins, smins, plays = META[day]
    data = DATA[day]
    pair = f"4A-T1-W01-D{day}"
    cid = "L" + pair

    def tag(focus, micro=False):
        return (c if micro else a)(pages, focus)

    groups = {
        "words": [word(text, opts.split("|"), answer, tag("秋日词汇辨别", i == 0))
                  for i, (text, opts, answer) in enumerate(data["words"])],
        "sentences": [sentence(display, heard, "same" if same else "different", tag("信息对应"))
                      for display, heard, same in data["sentences"]],
        "responses": [response(prompt, opts.split("|"), answer, tag("句型与问答对应", i == 0))
                      for i, (prompt, opts, answer) in enumerate(data["responses"])],
        "dialogues": [dialogue([["f" if i % 2 == 0 else "m", text] for i, text in enumerate(clips)],
                               question, opts.split("|"), answer, tag("秋日情境与细节"))
                      for clips, question, opts, answer in data["dialogues"]],
    }
    order = Random(day)
    for key in ("words", "responses", "dialogues"):
        questions = groups[key]
        positions = [(day + i) % 3 for i in range(len(questions))]
        order.shuffle(positions)
        for question, position in zip(questions, positions):
            options = question["options"]
            correct = options.pop(question["answer"])
            options.insert(position, correct)
            question["answer"] = position
    sections, next_id = [], 1
    for i, (sid, name, tip, key) in enumerate(SECTION_SPECS):
        section = make_section(sid, name, tip, plays[i], groups[key], cid, next_id)
        sections.append(section)
        next_id += len(section["questions"])
    last = make_section("passage", "听短文判断", "先听完整短文，再判断每句话是否正确", plays[4],
                        [passage_statement(text, answer, tag("短文取证")) for text, answer in data["statements"]],
                        cid, next_id)
    last.update(shared_audio=True, passage_audio=f"static/audio/listening/{cid}/p01.mp3",
                passage_transcript=[["n", data["passage"]]])
    sections.append(last)
    common = dict(weekly_batch_id="4A-T1-W01", study_pack=pair, pair_id=pair, publication_status="formal",
                  week=8, day=day-35, scope=f"4A Unit 6 {pages}", difficulty=difficulty)
    count = sum(len(section["questions"]) for section in sections)
    listening = dict(common, course_id=cid, title=f"四上·第{day}课｜Unit 6{title}（听力）",
                     course_type="weekly_test" if day == 40 else "training", est_minutes=lmins,
                     scoring={"per_question": 100//count, "total": 100},
                     test_audio=f"static/audio/listening/{cid}/hello.mp3",
                     test_transcript=[["n", "Hello! Can you hear me? Let us begin."]], sections=sections)
    qs = [dict(type="repeat", text=text, tag=tag("教材句型跟读")) for text in data["repeat"]]
    qs += [dict(type="qa", question=q, expected=expected, hint=f"用完整句回答：{hint}",
                tag=tag("引导问答与信息对应", i == 0))
           for i, (q, expected, hint) in enumerate(data["qa"])]
    for i, q in enumerate(qs, 1):
        q.update(id=i, audio=f"static/audio/speaking/S{pair}/q{i:02d}.mp3", parent_note=parent_note(q["tag"]))
    speaking = dict(common, course_id="S"+pair, title=f"四上·第{day}课｜Unit 6{title}（口语）",
                    course_type="weekly_review" if day == 40 else "training", est_minutes=smins, questions=qs)
    return listening, speaking


def documents(pairs):
    mapping = ["# Unit 6 D36–D40 教材与课程映射", "",
               "2026-11-06。使用确认版B008 p47–54。五组听力和口语同范围，按D34开放。",
               "", "| 课次 | 教材 | 听力／口语题数 | 内容 |", "|---|---|---:|---|"]
    parent = ["# Unit 6 D36–D40 家长版答案与原文", "", "听力原文为依据确认版教材编写的练习。", ""]
    for day, (lc, sc) in zip(META, pairs):
        title, pages, *_ = META[day]
        mapping.append(f"| D{day} | {pages} | {sum(len(s['questions']) for s in lc['sections'])}／{len(sc['questions'])} | {title} |")
        parent += [f"## D{day} {title}", "", f"教材范围 {pages}，配对 {lc['pair_id']}。", ""]
        for sec in lc["sections"]:
            parent += [f"### {sec['name']}（最多{sec['max_plays']}次）", ""]
            if sec.get("shared_audio"):
                parent += [sec["passage_transcript"][0][1], ""]
            parent += ["| 题号 | 原文／题干 | 答案 | 来源标签 |", "|---:|---|---|---|"]
            for q in sec["questions"]:
                parent.append(f"| {q['id']} | {transcript_text(q)} | {answer_text(q)} | {q['tag']} |")
            parent.append("")
        parent += ["### 跟读和引导问答", "", "| 题号 | 类型 | 示范／问句 | 目标句 | 中文提示 |", "|---:|---|---|---|---|"]
        for q in sc["questions"]:
            parent.append(f"| {q['id']} | {q['type']} | {q.get('text', q.get('question'))} | {q.get('text', q.get('expected'))} | {q.get('hint', '')} |")
        parent.append("")
    mapping += ["", "p47–49 农场、落叶、采果、南飞及秋日歌谣。p50 秋游观察。p51 How 感叹句和单复数。p52–53 塞罕坝故事。p54 秋天小诗与综合。",
                "", "p48 缺原音轨的喜好连线不猜配对。p51 缺图答案的选填不重构。p52–53 昔今对比按课文人物叙述。",
                "", "每课口语前6题跟读，后续为有完整中文目标提示的练习。C标签用于一般现在时、主谓和信息对应的滚动复习，未基于本批练习推断掌握。课程开放依据D34，学校实际授课进度另记。", ""]
    return "\n".join(mapping), "\n".join(parent)


def main():
    pairs = [build(day) for day in META]
    listening, speaking = map(list, zip(*pairs))
    for module, courses, sanitizer in (("listening", listening, child_listening),
                                       ("speaking", speaking, child_speaking)):
        catalog = []
        for course in courses:
            json_write(ROOT / f"content/{module}/{course['course_id']}.json", course)
            child = sanitizer(course)
            json_write(DRAFT / f"child/{module}/{course['course_id']}.json", child)
            catalog.append(child_catalog_entry(course, child))
        json_write(DRAFT / f"child/{module}/catalog.json", catalog)
    json_write(DRAFT / "audio-generation-plan.json", audio_plan(listening, speaking))
    packs = [
        dict(lesson=day, pair_id=lc["pair_id"], study_pack=lc["study_pack"], textbook_scope=lc["scope"],
             planned_difficulty=META[day][2], listening_course_id=lc["course_id"], speaking_course_id=sc["course_id"])
        for day, (lc, sc) in zip(META, pairs)
    ]
    json_write(DRAFT / "study-packs.json", dict(weekly_batch_id="4A-T1-W01", publication_status="formal",
                                                visible=True, authority_note="父JSON为唯一活动源", study_packs=packs))
    for suffix, body in zip(("教材与课程映射.md", "家长版答案原文.md"), documents(pairs)):
        Path(str(PREFIX) + suffix).write_text(body, encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
