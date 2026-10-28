# -*- coding: utf-8 -*-
"""2026-10-28 Unit 5 p39-46: ten paired courses, using existing formats."""
from pathlib import Path

from build_4a_starter_courses import (
    a, c, word, sentence, response, dialogue, passage_statement, parent_note,
    json_write, child_listening, child_speaking, answer_text, transcript_text,
)
from build_4a_unit2_courses import SECTION_SPECS, make_section, child_catalog_entry
from build_4a_unit1_unit2_review_courses import audio_plan

ROOT = Path(__file__).resolve().parents[1]
DRAFT = ROOT / "content/drafts/4A-T1-W01-UNIT5"
PREFIX = ROOT / "docs/course-batches/2026-10-28-4A-Unit5-D31-D35"
META = {
    31: ("社区场所·欢迎来访", "p39-p41", "L1", "L1", 12, 10, [2, 2, 2, 2, 3]),
    32: ("水乡游览·地点与细节", "p39-p42", "L1+", "L1", 14, 10, [2, 2, 2, 2, 3]),
    33: ("水乡与社区·单复数问答", "p39-p43", "L2", "L2", 17, 12, [2, 2, 2, 2, 3]),
    34: ("走进威尼斯·信息与理由", "p39-p45", "L2+", "L2", 21, 12, [1, 2, 2, 2, 3]),
    35: ("最喜欢的地方·单元综合", "p39-p46", "L3", "L3", 25, 12, [1, 1, 2, 2, 3]),
}

# Each heard text is an authored exercise. Missing textbook listening answers
# and photo-only choices are deliberately not reconstructed.
DATA = {
    31: {
        "words": [("museum", "museum|cinema|supermarket", 0), ("bridge", "shop|bridge|park", 1), ("neighbourhood", "museum|supermarket|neighbourhood", 2), ("a new cinema", "a new cinema|a big museum|a nice park", 0)],
        "sentences": [
            ("There is a nice park.", "There is a nice park.", True),
            ("There is a small museum.", "There is a big museum.", False),
            ("There is a new cinema.", "There is a new cinema.", True),
            ("Welcome to my school.", "Welcome to my neighbourhood.", False),
        ],
        "responses": [
            ("What is in your neighbourhood?", "There is a park.|It is green.|I can read.", 0),
            ("Is there a shop?", "It is a shop.|Yes, there is.|There are two.", 1),
            ("Where can you see a film?", "At the bridge.|At the park.|At the cinema.", 2),
            ("Is the museum big or small?", "It is big.|It is a museum.|There is one.", 0),
        ],
        "dialogues": [
            (["Welcome to my neighbourhood.", "Is there a park?", "Yes, there is a nice park."], "What place do they talk about?", "A park.|A shop.|A cinema.", 0),
            (["There is a museum here.", "Is it big?", "Yes, it is."], "What is the museum like?", "Small.|Big.|New.", 1),
            (["Is there a new shop?", "There is a shop, but the cinema is new."], "Which place is new?", "The shop.|The park.|The cinema.", 2),
            (["There is a library and a supermarket.", "Can we buy food at the supermarket?", "Yes, we can."], "Where can they buy food?", "At the supermarket.|At the library.|At the bridge.", 0),
        ],
        "passage": "Welcome to my neighbourhood. There is a nice park and a shop. There is a big museum and a library. There is a new cinema and a supermarket. It is nice to go around my neighbourhood.",
        "statements": [("There is a nice park.", True), ("The museum is small.", False), ("There is a new cinema.", True), ("There is no supermarket.", False)],
        "repeat": ["Welcome to my neighbourhood.", "There is a nice park and a shop.", "There is a big museum and a library.", "There is a new cinema and a supermarket.", "This is my lovely neighbourhood.", "It is nice to go around my neighbourhood."],
        "qa": [
            ("Is there a park in the chant?", "Yes, there is a nice park.", "是的，有一个漂亮的公园。"),
            ("What is the museum like in the chant?", "It is a big museum.", "它是一个大博物馆。"),
            ("Which place is new in the chant?", "The cinema is new.", "电影院是新的。"),
            ("What can you say to welcome a visitor?", "Welcome to my neighbourhood.", "欢迎来到我的社区。"),
        ],
    },
    32: {
        "words": [("a boat trip", "a photo|a boat trip|an old house", 1), ("old bridges", "old houses|old shops|old bridges", 2), ("a beautiful river", "a beautiful river|a big museum|a new cinema", 0), ("out of battery", "over the bridge|out of battery|by the water", 1)],
        "sentences": [
            ("They want to go on a boat trip.", "They want to go on a boat trip.", True),
            ("The two bridges are forty years old.", "The two bridges are over four hundred years old.", False),
            ("The museum tells the story of the old town.", "The museum tells the story of the old town.", True),
            ("The camera has a full battery.", "The camera is out of battery.", False),
        ],
        "responses": [
            ("What can we do on the river?", "Take a boat trip.|Visit a cinema.|Read in a library.", 0),
            ("Are there any nice old bridges around?", "Yes, it is.|Yes, there are.|Yes, there is.", 1),
            ("What tells the story of the old town?", "The camera.|The cinema.|The museum.", 2),
            ("Why can we not use the camera now?", "It is out of battery.|It is very old.|It is over the river.", 0),
        ],
        "dialogues": [
            (["Look, there is a beautiful river.", "Let us go on a boat trip."], "What do they want to do?", "Visit a library.|Take a boat trip.|Go to a cinema.", 1),
            (["Are there any old bridges?", "Yes, two beautiful bridges near here are over four hundred years old."], "How many old bridges are mentioned?", "Two.|Four.|One.", 0),
            (["I like the old houses and shops.", "They look nice. Let us take some photos."], "What do they want to photograph?", "New buses.|A new cinema.|Old houses and shops.", 2),
            (["Is there a museum here?", "Yes, there is. Let us take a photo there.", "Oh no! My camera is out of battery."], "What is the problem?", "There is no museum.|The camera is out of battery.|There is no river.", 1),
        ],
        "passage": "Shenshen, her mum and Yaoyao are visiting an old water town. There is a beautiful river. They want to go on a boat trip. Two bridges near them are over four hundred years old. The museum tells the story of the old town. They want to take a photo there, but the camera is out of battery.",
        "statements": [("They are visiting a water town.", True), ("They want to take a bus trip.", False), ("Two bridges are over four hundred years old.", True), ("The camera works at the museum.", False)],
        "repeat": ["Look, there is a beautiful river.", "Let us go on a boat trip.", "Are there any nice old bridges around?", "Two beautiful bridges near here are over four hundred years old.", "The museum tells the story of the old town.", "Oh no! My camera is out of battery."],
        "qa": [
            ("Is there a museum in the water town?", "Yes, there is a museum.", "是的，有一个博物馆。"),
            ("How old are the two bridges?", "They are over four hundred years old.", "它们有四百多年的历史。"),
            ("What does the museum tell?", "It tells the story of the old town.", "它讲述这个古镇的故事。"),
            ("What is wrong with the camera?", "It is out of battery.", "它没电了。"),
        ],
    },
    33: {
        "words": [("a museum", "a museum|some museums|some bridges", 0), ("any buses", "any bridges|any buses|any shops", 1), ("a new bridge", "an old bridge|a new cinema|a new bridge", 2), ("some old houses", "some old houses|some old bridges|some new shops", 0)],
        "sentences": [
            ("There is a museum in the water town.", "There is a museum in the water town.", True),
            ("There is a cinema in the water town.", "There is no cinema in the water town.", False),
            ("There are some old bridges around.", "There are some old bridges around.", True),
            ("There are some buses in the water town.", "There are no buses in the water town.", False),
        ],
        "responses": [
            ("Is there a cinema in the water town?", "No, there is not.|No, there are not.|Yes, it is.", 0),
            ("Are there any buses in the water town?", "No, there is not.|No, there are not.|No, it is not.", 1),
            ("Is there a museum in the water town?", "Yes, there are.|Yes, it is.|Yes, there is.", 2),
            ("Are there any nice old bridges around?", "Yes, there are.|Yes, there is.|Yes, they can.", 0),
        ],
        "dialogues": [
            (["Is there a cinema in the water town?", "No, there is not. But there is a museum."], "Which place can they visit?", "A cinema.|A museum.|A supermarket.", 1),
            (["Are there any old bridges in your neighbourhood?", "No, there are not. But there is a new bridge."], "What kind of bridge is in this neighbourhood?", "A new bridge.|An old bridge.|No bridge.", 0),
            (["Are there any buses in the water town?", "No, there are not.", "Let us go on a boat trip."], "How do they plan to travel?", "By bus.|By car.|By boat.", 2),
            (["Is there a museum in your neighbourhood?", "Yes, a very nice one.", "Are there any old bridges?", "No, there are not."], "What is in this neighbourhood?", "Old bridges.|A museum.|A cinema.", 1),
        ],
        "passage": "We are in the water town. There is a museum, but there is no cinema. There are some nice old bridges, but there are no buses. My neighbourhood is different. There is a new bridge and a very nice museum. There are no old bridges in my neighbourhood.",
        "statements": [("There is a museum in the water town.", True), ("There are buses in the water town.", False), ("There is a new bridge in the speaker's neighbourhood.", True), ("There are old bridges in the speaker's neighbourhood.", False)],
        "repeat": ["Is there a museum here? Yes, there is.", "Is there a cinema in the water town? No, there is not.", "Are there any nice old bridges around? Yes, there are.", "Are there any buses in the water town? No, there are not.", "There is a new bridge in my neighbourhood.", "There is a very nice museum too."],
        "qa": [
            ("Are there any buses in the water town?", "No, there are not.", "不，没有。"),
            ("Is there a cinema in the water town?", "No, there is not.", "不，没有。"),
            ("Is there a museum in the water town?", "Yes, there is.", "是的，有。"),
            ("Are there any old bridges in the water town?", "Yes, there are.", "是的，有。"),
            ("What kind of bridge is in the neighbourhood in the example?", "There is a new bridge.", "有一座新桥。"),
            ("What other place is in that neighbourhood?", "There is a very nice museum too.", "还有一个非常漂亮的博物馆。"),
        ],
    },
    34: {
        "words": [("Italy", "Italy|Venice|a water town", 0), ("colourful bridges", "old bridges|colourful bridges|a new bridge", 1), ("a gondola", "a camera|a museum|a gondola", 2), ("by the water", "by the water|over the river|in the park", 0), ("interesting shops", "colourful houses|interesting shops|old trees", 1)],
        "sentences": [
            ("Venice is a famous city in Italy.", "Venice is a famous city in Italy.", True),
            ("People go around Venice by bus.", "People go around Venice by boat.", False),
            ("The bridges are in different colours.", "The bridges are in different colours.", True),
            ("There are no restaurants by the water.", "There are many restaurants by the water.", False),
            ("Venice is also famous for its museums.", "Venice is also famous for its museums.", True),
        ],
        "responses": [
            ("Where is Venice?", "It is in Italy.|It is in the park.|It is a museum.", 0),
            ("How do people go around Venice?", "By bus.|By boat.|By car.", 1),
            ("What is a gondola?", "A colourful bridge.|An interesting shop.|A special boat.", 2),
            ("Why do you like the bridges in Venice?", "They look different and colourful.|They are boats.|They are in a museum.", 0),
            ("Where are the houses in Venice?", "Over the park.|By the water.|In a gondola.", 1),
        ],
        "dialogues": [
            (["Venice is a famous city.", "Is it in Italy?", "Yes, it is."], "Where is Venice?", "In Italy.|In the old museum.|In the park.", 0),
            (["How do people go around the city?", "By boat. This special boat is called a gondola."], "What is a gondola?", "A bridge.|A boat.|A restaurant.", 1),
            (["I like the bridges in Venice.", "Why?", "They look different and colourful."], "Why does the speaker like the bridges?", "They are all new.|They are all tall.|They look colourful.", 2),
            (["Are there any restaurants by the water?", "Yes, many. There are interesting shops too."], "Which two places are mentioned?", "Restaurants and shops.|Parks and cinemas.|Schools and libraries.", 0),
            (["The houses in Venice are all by the water.", "Do they look colourful?", "Yes. I like them."], "What does the speaker like?", "The buses.|The houses.|The cameras.", 1),
        ],
        "passage": "Venice is a famous city in Italy. Its houses are by the water and look colourful. There are a lot of bridges in different colours. People go around the city by boat. A special boat is called a gondola. There are many restaurants by the water and interesting shops. Venice is also famous for its museums.",
        "statements": [("Venice is in Italy.", True), ("All the bridges are the same colour.", False), ("A gondola is a special boat.", True), ("There are no interesting shops in Venice.", False), ("Venice is famous for its museums too.", True)],
        "repeat": ["Venice is a famous city in Italy.", "The houses are all by the water and look colourful.", "There are a lot of bridges in different colours.", "People in Venice go around the city by boat.", "This special boat is called a gondola.", "Venice is also famous for its museums."],
        "qa": [
            ("Are there any bridges in Venice?", "Yes, there are a lot of bridges.", "是的，有很多桥。"),
            ("Where is Venice?", "Venice is in Italy.", "威尼斯在意大利。"),
            ("How do people go around Venice?", "They go around the city by boat.", "他们乘船在城里游览。"),
            ("What is a gondola?", "It is a special boat.", "它是一种特别的船。"),
            ("Why do you like the bridges in Venice?", "They look different and colourful.", "它们看起来各不相同，色彩缤纷。"),
            ("Where are many restaurants in Venice?", "They are by the water.", "它们在水边。"),
        ],
    },
    35: {
        "words": [("a playground", "a playground|a supermarket|a museum", 0), ("old trees", "old shops|old trees|old bridges", 1), ("a photo of my favourite place", "a photo of a boat|a photo of a bridge|a photo of my favourite place", 2), ("nice and clean", "nice and clean|old and small|new and colourful", 0), ("every week", "every day|every week|every month", 1)],
        "sentences": [
            ("There is a big park in the neighbourhood.", "There is a big park in the neighbourhood.", True),
            ("The old trees in the park are short.", "The old trees in the park are very tall.", False),
            ("There is a big playground in the park.", "There is a big playground in the park.", True),
            ("The child goes there with Dad every day.", "The child goes there with Mum every week.", False),
            ("People go around Venice by boat.", "People go around Venice by boat.", True),
        ],
        "responses": [
            ("Are there any old trees in the park?", "Yes, there are.|Yes, there is.|Yes, it is.", 0),
            ("Is there a playground in the park?", "Yes, there are.|Yes, there is.|Yes, they are.", 1),
            ("Why do you like the park in the example?", "It is a gondola.|It is out of battery.|It is nice and clean.", 2),
            ("Who goes to the park with the child in the example?", "The child's mum.|The child's brother.|The child's dad.", 0),
            ("What do you need to take a photo of your favourite place?", "A boat.|A camera.|A bridge.", 1),
        ],
        "dialogues": [
            (["Look at my photo. This park is my favourite place.", "Is it in your neighbourhood?", "Yes. It is nice and clean."], "What is the photo of?", "A park.|A museum.|A cinema.", 0),
            (["Are there any old trees in the park?", "Yes, and they are very tall.", "Is there a playground?", "Yes, a big one."], "Which two things are in the park?", "Shops and bridges.|Old trees and a playground.|Boats and restaurants.", 1),
            (["I go to this park with my mum every week.", "Do you go with your dad every day?", "No, with my mum every week."], "When does the child go to the park?", "Every day.|Every month.|Every week.", 2),
            (["Is this photo of Venice?", "Yes. Look at the colourful houses by the water.", "I can see a gondola too."], "Which detail helps them recognise Venice?", "A gondola.|A playground.|A supermarket.", 0),
            (["Let us take a photo at the water town museum.", "My camera is out of battery.", "Then we cannot use it now."], "Why can they not use this camera?", "The museum is closed.|It is out of battery.|There is no river.", 1),
        ],
        "passage": "Look at this photo of my favourite place. It is a big park in my neighbourhood. It is nice and clean. There are some old trees, and they are very tall. There is a big playground too. I go there with my mum every week. My friend wants to play there with her brother. We can introduce the park and answer questions about it.",
        "statements": [("The favourite place is a park.", True), ("The park is small and dirty.", False), ("There are tall old trees in the park.", True), ("There is no playground in the park.", False), ("The speaker goes there with Mum every week.", True)],
        "repeat": ["This is a photo of my favourite place.", "It is a big park in my neighbourhood.", "It is nice and clean.", "There are some very tall old trees in it.", "There is a big playground in the park.", "I go there with my mum every week."],
        "qa": [
            ("Is there a playground in the park in the example?", "Yes, there is a big playground.", "是的，有一个大游乐场。"),
            ("Are there any old trees in that park?", "Yes, there are. They are very tall.", "是的，有。它们非常高。"),
            ("What is the park like in the example?", "It is nice and clean.", "它漂亮又干净。"),
            ("Who goes to the park with the child every week?", "The child goes there with Mum.", "这个孩子和妈妈一起去那里。"),
            ("Why do people like the bridges in Venice?", "They look different and colourful.", "它们看起来各不相同，色彩缤纷。"),
            ("Why can they not use the camera at the museum?", "The camera is out of battery.", "相机没电了。"),
        ],
    },
}


def build(day):
    title, pages, _, difficulty, lmins, smins, plays = META[day]
    data = DATA[day]
    pair = f"4A-T1-W01-D{day}"
    cid = "L" + pair
    def tag(focus, micro=False):
        return (c if micro else a)(pages, focus)
    groups = {
        "words": [word(text, opts.split("|"), answer, tag("场所词汇辨别", i == len(data["words"])-1)) for i, (text, opts, answer) in enumerate(data["words"])],
        "sentences": [sentence(display, heard, "same" if same else "different", tag("句子信息对应")) for display, heard, same in data["sentences"]],
        "responses": [response(prompt, opts.split("|"), answer, tag("单复数与问答对应", i == 1)) for i, (prompt, opts, answer) in enumerate(data["responses"])],
        "dialogues": [dialogue([["f" if i % 2 == 0 else "m", text] for i, text in enumerate(clips)], question, opts.split("|"), answer, tag("地点与细节整合")) for clips, question, opts, answer in data["dialogues"]],
    }
    sections, next_id = [], 1
    for i, (sid, name, tip, key) in enumerate(SECTION_SPECS):
        section = make_section(sid, name, tip, plays[i], groups[key], cid, next_id)
        sections.append(section)
        next_id += len(section["questions"])
    last = make_section("passage", "听短文判断", "先听完整短文，再判断每句话是否正确", plays[4], [passage_statement(text, answer, tag("短文取证")) for text, answer in data["statements"]], cid, next_id)
    last.update(shared_audio=True, passage_audio=f"static/audio/listening/{cid}/p01.mp3", passage_transcript=[["n", data["passage"]]])
    sections.append(last)
    common = dict(weekly_batch_id="4A-T1-W01", study_pack=pair, pair_id=pair, publication_status="formal", week=7, day=day-30, scope=f"4A Unit 5 {pages}", difficulty=difficulty)
    count = sum(len(s["questions"]) for s in sections)
    listening = dict(common, course_id=cid, title=f"四上·第{day}课｜Unit 5{title}（听力）", course_type="weekly_test" if day == 35 else "training", est_minutes=lmins, scoring={"per_question": 100//count, "total": 100}, test_audio=f"static/audio/listening/{cid}/hello.mp3", test_transcript=[["n", "Hello! Can you hear me? Let us begin."]], sections=sections)
    qs = [dict(type="repeat", text=text, tag=tag("教材句型跟读")) for text in data["repeat"]]
    qs += [dict(type="qa", question=q, expected=expected, hint=f"用完整句回答：{hint}", tag=tag("引导问答与信息对应", i == 0)) for i, (q, expected, hint) in enumerate(data["qa"])]
    for i, q in enumerate(qs, 1):
        q.update(id=i, audio=f"static/audio/speaking/S{pair}/q{i:02d}.mp3", parent_note=parent_note(q["tag"]))
    speaking = dict(common, course_id="S"+pair, title=f"四上·第{day}课｜Unit 5{title}（口语）", course_type="weekly_review" if day == 35 else "training", est_minutes=smins, questions=qs)
    return listening, speaking


def documents(pairs):
    mapping = ["# Unit 5 D31–D35 教材与课程映射", "", "日期：2026-10-28。家长明确要求U5听力、口语各5课，沿用成熟批次结构及D34默认formal可见流程。", "", "| 课次 | 教材 | 听力/口语题量 | 难度 | 内容 |", "|---|---|---:|---|---|"]
    parent = ["# Unit 5 D31–D35 家长版答案原文", "", "家长专用；自编听力，不是教材缺失音轨的答案。", ""]
    for day, (lc, sc) in zip(META, pairs):
        title, pages, level, *_ = META[day]
        mapping.append(f"| D{day} | Unit 5 {pages} | {sum(len(s['questions']) for s in lc['sections'])}/{len(sc['questions'])} | {level} | {title} |")
        parent += [f"## D{day}：{title}", "", f"配对：{lc['pair_id']}；教材：{pages}。", ""]
        for sec in lc["sections"]:
            parent += [f"### {sec['name']}（最多{sec['max_plays']}次）", ""]
            if sec.get("shared_audio"):
                parent += ["短文原文：" + sec["passage_transcript"][0][1], ""]
            parent += ["| 题号 | 原文/题干 | 答案 | 来源标签 |", "|---:|---|---|---|"]
            for q in sec["questions"]:
                parent.append(f"| {q['id']} | {transcript_text(q)} | {answer_text(q)} | {q['tag']} |")
            parent.append("")
        parent += ["### 跟读与口语", "", "| 题号 | 类型 | 示范/问句 | 目标句 | 中文提示 |", "|---:|---|---|---|---|"]
        for q in sc["questions"]:
            parent.append(f"| {q['id']} | {q['type']} | {q.get('text', q.get('question'))} | {q.get('text', q.get('expected'))} | {q.get('hint', '')} |")
        parent.append("")
    mapping += ["", "## 来源及教学边界", "", "- 权威源：确认版B007 p39–46，与全册最终转录同页段一致；不使用历史错误版本PDF，也不进入U6。", "- p39–41场所词与chant；p42水乡对话及camera out of battery；p43 is/are there肯否问答；p44–45威尼斯；p46公园照片介绍。", "- p40听力空格没有原音轨，不能确认Shenshen/Minmin最喜欢哪里；p43勾图题不臆造照片序号。", "- 威尼斯仅使用教材的Italy、临水房屋、多彩桥、gondola、餐厅、商店、博物馆等明文事实；不自行补充历史或交通禁令。", "- D33社区对比及D35公园均是教材示例/自编叙述，不代表孩子真实住址、喜好或习惯。p46未明确姓名、性别的介绍者不擅自具名。", "- 110听力题、56口语题；前6题repeat，其余为带完整中文目标句提示的引导QA；不是无提示自由口语测量。", "- 难度通过信息跨度、相近选项、单复数/肯否区分、两场景对比和后两课题量递增；播放次数沿用成熟梯度，D35综合。", "- 每课仅2个听力C标签与1个口语C标签，复现中性信息对应、is/are/单复数旧型；没有新的formal弱项摘要，不虚称20%个性化，也不从测试推断掌握。", "- 音频与旧批次同音色、同语速；154成品目标。课程JSON是唯一活动源，child/计划/家长答案为派生产物。", "- 不修改录音、评分、门控、身份、会话或学习进度核心；不生成成绩与儿童录音。", "- 制作、发布、实际学习和掌握分别登记；桌面工程检查不能替代真实iPad/家庭网络验收。", ""]
    return "\n".join(mapping), "\n".join(parent)


def main():
    pairs = [build(day) for day in META]
    listening, speaking = map(list, zip(*pairs))
    for module, courses, sanitizer in (("listening", listening, child_listening), ("speaking", speaking, child_speaking)):
        catalog = []
        for course in courses:
            json_write(ROOT / f"content/{module}/{course['course_id']}.json", course)
            child = sanitizer(course)
            json_write(DRAFT / f"child/{module}/{course['course_id']}.json", child)
            catalog.append(child_catalog_entry(course, child))
        json_write(DRAFT / f"child/{module}/catalog.json", catalog)
    json_write(DRAFT / "audio-generation-plan.json", audio_plan(listening, speaking))
    json_write(DRAFT / "study-packs.json", dict(weekly_batch_id="4A-T1-W01", publication_status="formal", visible=True, authority_note="父JSON为唯一活动源；本目录为派生产物。", study_packs=[dict(lesson=day, pair_id=lc["pair_id"], study_pack=lc["study_pack"], textbook_scope=lc["scope"], planned_difficulty=META[day][2], listening_course_id=lc["course_id"], speaking_course_id=sc["course_id"]) for day, (lc, sc) in zip(META, pairs)]))
    mapping, parent = documents(pairs)
    for suffix, body in (("教材与课程映射.md", mapping), ("家长版答案原文.md", parent)):
        Path(str(PREFIX) + suffix).write_text(body, encoding="utf-8", newline="\n")
    print("Built Unit 5 D31-D35: 110 listening, 56 speaking, 154 audio targets.")


if __name__ == "__main__":
    main()
