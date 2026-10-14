# -*- coding: utf-8 -*-
"""Build the D36-approved Unit 4 p31-p38 D26-D30 package.

Parent JSON is authoritative; child copies and documentation are derived.
Run from the project root: python tools/build_4a_unit4_courses.py
"""
from pathlib import Path

from build_4a_starter_courses import (
    a, c, word, sentence, response, dialogue, passage_statement, parent_note,
    json_write, child_listening, child_speaking, answer_text, transcript_text,
)
from build_4a_unit2_courses import SECTION_SPECS, make_section, child_catalog_entry
from build_4a_unit1_unit2_review_courses import audio_plan

ROOT = Path(__file__).resolve().parents[1]
DRAFT = ROOT / "content/drafts/4A-T1-W01-UNIT4"
PREFIX = ROOT / "docs/course-batches/2026-10-13-4A-Unit4-D26-D30"
BATCH = "4A-T1-W01"
META = {
    26: ("Unit 4生日词汇与活动", "p31-p32", "L1", "L1", 12, 10, [2, 2, 2, 2, 3]),
    27: ("Unit 4生日邀请·时间与地点", "p31-p33", "L1+", "L1", 14, 10, [2, 2, 2, 2, 3]),
    28: ("Unit 4爱的来信·感谢与传统", "p31-p35", "L2", "L2", 17, 12, [2, 2, 2, 2, 3]),
    29: ("Unit 4生日面条·故事整合", "p31-p37", "L2+", "L2", 21, 12, [1, 2, 2, 2, 3]),
    30: ("Unit 4生日会计划·单元综合", "p31-p38", "L3", "L3", 25, 12, [1, 1, 2, 2, 3]),
}

# Each tuple holds explicit heard content, distractors and answer. These are
# authored exercises, not reconstructed answers to textbook Listen tasks.
DATA = {
    26: {
        "words": [
            ("invitation", "invitation|activity|party", 0),
            ("noodles", "letter|noodles|egg", 1),
            ("share a cake", "read a letter|play games|share a cake", 2),
            ("letter", "letter|party|activity", 0),
        ],
        "sentences": [
            ("I can play games at the birthday party.", "I can play games at the birthday party.", True),
            ("I can act as a bee.", "I can act as a cat.", False),
            ("We can share a cake.", "We can share a cake.", True),
            ("I can read a letter.", "I can write a letter.", False),
        ],
        "responses": [
            ("What can you do at the birthday party?", "I can play games.|It is a letter.|It is an egg.", 0),
            ("Can you share a cake?", "It is a party.|Yes, I can.|It is a letter.", 1),
            ("What can you read?", "A cake.|An egg.|A letter.", 2),
            ("What can you write?", "A letter.|A cake.|Noodles.", 0),
        ],
        "dialogues": [
            (["I can act as a bee.", "I can act as a cat."], "What can the girl act as?", "A bee.|A cat.|An egg.", 0),
            (["We can share a cake.", "Yes, at the birthday party."], "What can they share?", "A letter.|A cake.|An invitation.", 1),
            (["I can write a letter.", "I can read your letter."], "What can the boy do?", "Eat a cake.|Play games.|Read a letter.", 2),
            (["I can play games at the party.", "I can eat a cake."], "What can the girl do?", "Play games.|Write a letter.|Act as a cat.", 0),
        ],
        "passage": "We have a birthday party. I can act as a bee. My friend can act as a cat. We can play games and share a cake. I can write a letter, and my friend can read it.",
        "statements": [("The speaker can act as a bee.", True), ("The friend can act as a bee.", False), ("They can share a cake.", True), ("The speaker cannot write a letter.", False)],
        "repeat": ["I can play games at the birthday party.", "We can share a cake at the party.", "I can write a letter.", "My friend can read a letter.", "I can act as a bee.", "My friend can act as a cat."],
        "qa": [
            ("What can you read?", "I can read a letter.", "我能读一封信。"),
            ("What can you share at the party?", "We can share a cake.", "我们能分享一个蛋糕。"),
            ("What can you do at the party?", "I can play games at the party.", "我能在聚会上玩游戏。"),
            ("What can you act as?", "I can act as a bee.", "我能扮演一只蜜蜂。"),
        ],
    },
    27: {
        "words": [("birthday invitation", "birthday invitation|birthday activity|birthday cake", 0), ("nine a.m.", "one p.m.|nine a.m.|three p.m.", 1), ("School Building Two", "School Building One|School Building Two|Class One", 1), ("bring a letter", "read a letter|write a letter|bring a letter", 2)],
        "sentences": [
            ("The party is at nine a.m.", "The party is at nine a.m.", True),
            ("The party is on the twenty-eighth of October.", "The party is on the twenty-seventh of October.", False),
            ("The party is in the hall in School Building Two.", "The party is in the hall in School Building Two.", True),
            ("Parents bring a cake to their children.", "Parents bring a letter to their children.", False),
        ],
        "responses": [
            ("What is this?", "It is our birthday party invitation.|I can play games.|It is at nine a.m.", 0),
            ("Where is the birthday party?", "At nine a.m.|In the hall in School Building Two.|On the twenty-seventh of October.", 1),
            ("What can parents watch at the party?", "They can watch a play.|They can read a cake.|They can write noodles.", 0),
            ("What should parents bring?", "A big cake.|A game.|A letter to their children.", 2),
        ],
        "dialogues": [
            (["Welcome to our birthday party.", "What time is it?", "It is at nine a.m."], "What time is the party?", "Nine a.m.|Nine p.m.|One p.m.", 0),
            (["The invitation says the twenty-seventh of October.", "Good. We can watch a play there."], "When is the party in the invitation?", "The twenty-eighth of October.|The twenty-seventh of October.|The twenty-sixth of October.", 1),
            (["Is the party in School Building One?", "No, it is in the hall in School Building Two."], "Where is the party?", "The hall in Building One.|The classroom in Building Two.|The hall in Building Two.", 2),
            (["Please bring a letter to your child.", "All right. Can we share a cake?", "Yes, a big cake."], "What should the parent bring?", "A letter.|A cake.|Noodles.", 0),
        ],
        "passage": "This is the birthday invitation from Class One. The students are turning ten. The party is at nine a.m. on the twenty-seventh of October, in the hall in School Building Two. Parents can watch a play and share a big cake. Please bring a letter to your child.",
        "statements": [("The students are turning ten.", True), ("The party is at nine p.m.", False), ("The party is in School Building Two.", True), ("Parents should bring noodles.", False)],
        "repeat": ["It is our birthday party invitation.", "Welcome to our birthday party.", "The party is at nine a.m. on the twenty-seventh of October.", "The party is in the hall in School Building Two.", "We can watch a play and share a big cake.", "Please bring a letter to your child."],
        "qa": [
            ("Where is the party in the invitation?", "It is in the hall in School Building Two.", "它在二号教学楼的礼堂。"),
            ("What time is the party?", "It is at nine a.m.", "它在上午九点。"),
            ("What can parents do at the party?", "They can watch a play and share a big cake.", "他们能看一出戏并分享一个大蛋糕。"),
            ("What should parents bring?", "They should bring a letter to their children.", "他们应该带一封给孩子们的信。"),
        ],
    },
    28: {
        "words": [("tradition", "tradition|invitation|activity", 0), ("parents' letters", "parents' letters|birthday cakes|birthday games", 0), ("family photo", "family photo|birthday invitation|football player", 0), ("read a letter", "bring a letter|read a letter|write a letter", 1)],
        "sentences": [
            ("Minmin's father writes about a football player.", "Minmin's father writes about a football player.", True),
            ("The mother writes many words in her letter.", "The mother does not write a word in her letter.", False),
            ("The mother draws some pictures.", "The mother draws some pictures.", True),
            ("Shenshen thanks Mum and Dad for a cake.", "Shenshen says, Thank you for all the time you spend with me.", False),
        ],
        "responses": [
            ("What does Minmin's father say Minmin can be?", "A doctor.|A football player.|A teacher.", 1),
            ("What does the mother put in the letter with no words?", "Some pictures.|Some eggs.|Some games.", 0),
            ("What do the children say to their parents?", "See you at school.|Thank you, Mum and Dad.|Welcome to the hall.", 1),
            ("What is a birthday tradition in the book?", "To read a cake.|To write noodles.|To take a family photo.", 2),
        ],
        "dialogues": [
            (["My father writes, You can be a great football player, Minmin.", "He loves you and your dream."], "Who is the father's letter for?", "Minmin.|Miss Li.|Grandma.", 0),
            (["My mother does not write a word.", "Does she draw pictures?", "Yes. I like this letter."], "What is in the mother's letter?", "Many words.|Some pictures.|An invitation.", 1),
            (["Let us read our parents' letters.", "It is a tradition at our group birthday party.", "Then let us say thank you."], "What do they do after reading the letters?", "They cook noodles.|They watch a play.|They thank their parents.", 2),
            (["Thank you for all the time you spend with me.", "Who is your card for?", "It is for Mum and Dad."], "Who is the thank-you card for?", "Mum and Dad.|A football player.|Class One.", 0),
        ],
        "passage": "At the group birthday party, the children read their parents' letters. Minmin's father says Minmin can be a great football player. One mother writes no words, but she draws some pictures. The child likes the letter. Shenshen writes a card to Mum and Dad. Shenshen says, Thank you for all the time you spend with me.",
        "statements": [("The children read their parents' letters.", True), ("Minmin's father says Minmin can be a doctor.", False), ("One letter has pictures but no words.", True), ("Shenshen's card is for Miss Li.", False)],
        "repeat": ["It is a tradition to read parents' letters at our group birthday party.", "You can be a great football player, Minmin.", "Work hard and your dreams will come true.", "My mother writes no words, but she draws some pictures.", "Thank you for all the time you spend with me.", "It is a tradition to take a family photo on your birthday."],
        "qa": [
            ("Who is Minmin's father's letter for?", "It is for Minmin.", "它是给Minmin的。"),
            ("What is in the mother's letter with no words?", "There are some pictures in the letter.", "信里有一些图画。"),
            ("What do you say to your parents?", "Thank you, Mum and Dad. I love you.", "谢谢你们，妈妈和爸爸。我爱你们。"),
            ("What is the tradition at the group birthday party?", "It is a tradition to read parents' letters.", "读父母的信是一项传统。"),
            ("What does Shenshen say to Mum and Dad?", "Thank you for all the time you spend with me.", "感谢你们陪伴我的所有时间。"),
            ("What photo can you take on your birthday?", "I can take a family photo on my birthday.", "我能在生日时拍一张全家福。"),
        ],
    },
    29: {
        "words": [("a bowl of noodles", "a bowl of noodles|a bowl of eggs|a birthday cake", 0), ("two eggs", "one egg|two eggs|three eggs", 1), ("soup noodles", "birthday letters|soup noodles|birthday hats", 1), ("good health", "a big cake|good health|a family photo", 1), ("tomatoes", "tomatoes|noodles|vegetables", 0)],
        "sentences": [
            ("Minmin turns ten, and Mum cooks noodles for him.", "Minmin turns ten, and Mum cooks noodles for him.", True),
            ("Minmin's bowl has one egg and no tomatoes.", "Minmin's bowl has two eggs and some tomatoes.", False),
            ("Grandma had only soup noodles when she was ten.", "Grandma had only soup noodles when she was ten.", True),
            ("Grandma says there was no love in the bowl.", "Grandma says there was lots of love in the bowl.", False),
            ("Parents wish their child good health and a long, happy life.", "Parents wish their child good health and a long, happy life.", True),
        ],
        "responses": [
            ("Who cooks birthday noodles for Minmin?", "His mother.|His father.|His grandma.", 0),
            ("How many eggs are in Minmin's noodles?", "One.|Two.|Three.", 1),
            ("What did Grandma have at ten?", "A big cake.|Noodles with two eggs.|Only soup noodles.", 2),
            ("What do parents wish their child?", "Good health and a long, happy life.|A birthday invitation.|A football game.", 0),
            ("What was in Grandma's bowl besides soup noodles?", "Two eggs.|Lots of love.|Some tomatoes.", 1),
        ],
        "dialogues": [
            (["Minmin turns ten today.", "His mother cooks birthday noodles for him.", "There are two eggs in the bowl."], "Who cooks the noodles?", "Grandma.|Mum.|Minmin.", 1),
            (["Are there tomatoes in Minmin's bowl?", "Yes, and two eggs and other vegetables."], "Which food is in Minmin's bowl?", "Tomatoes.|A cake.|Gifts.", 0),
            (["Did you have noodles at ten, Grandma?", "Yes, but only soup noodles.", "Minmin is surprised."], "How does Minmin feel?", "Angry.|Afraid.|Surprised.", 2),
            (["Grandma had only soup noodles.", "Was there love in the bowl?", "Yes, lots of love."], "What does Grandma remember?", "A bowl full of eggs.|Lots of love.|A birthday show.", 1),
            (["I want to put eggs in my mother's birthday noodles.", "That is your plan for her birthday."], "Whose noodles does the girl plan to make?", "Her mother's.|Her grandma's.|Minmin's.", 0),
        ],
        "passage": "Minmin turns ten today. Mum cooks a bowl of noodles with two eggs, some tomatoes and other vegetables. Grandma had noodles when she was ten too, but she had only soup noodles. Minmin is surprised. Grandma says there was lots of love in the bowl. Parents wish their child good health and a long and happy life.",
        "statements": [("Minmin turns ten today.", True), ("Mum puts three eggs in his noodles.", False), ("Grandma had only soup noodles at ten.", True), ("Grandma says there was no love in her bowl.", False), ("Parents wish their child good health.", True)],
        "repeat": ["Minmin turns ten today, and Mum cooks noodles for him.", "There are two eggs, some tomatoes and other vegetables in his bowl.", "It is a tradition to eat a bowl of noodles on your birthday.", "Grandma had only soup noodles when she was ten.", "It may not be much, but there was lots of love in the bowl.", "Parents wish their child good health and a long and happy life."],
        "qa": [
            ("How many eggs are in Minmin's bowl?", "There are two eggs in his bowl.", "他的碗里有两个鸡蛋。"),
            ("Who cooks birthday noodles for Minmin?", "Mum cooks birthday noodles for Minmin.", "妈妈为Minmin煮生日面条。"),
            ("What vegetables are named in Minmin's noodles?", "There are some tomatoes in his noodles.", "他的面条里有一些番茄。"),
            ("What did Grandma have at ten?", "She had only soup noodles.", "她只有汤面。"),
            ("What does Grandma say about her bowl?", "There was lots of love in the bowl.", "碗里有很多爱。"),
            ("What do parents wish their child?", "They wish their child good health and a long and happy life.", "他们祝愿孩子身体健康，拥有长久而幸福的生活。"),
        ],
    },
    30: {
        "words": [("group birthday party", "group birthday party|family birthday noodles|birthday invitation", 0), ("a camera", "a letter|a camera|a birthday hat", 1), ("read parents' letters", "give birthday cards|read parents' letters|take a group photo", 1), ("one p.m. to three p.m.", "nine a.m. to one p.m.|one p.m. to three p.m.|three p.m. to nine p.m.", 1), ("birthday hats", "birthday hats|birthday cards|birthday letters", 0)],
        "sentences": [
            ("The project plan is for Monday, the twenty-eighth of October.", "The project plan is for Monday, the twenty-eighth of October.", True),
            ("The invitation and the project plan both say nine a.m.", "The invitation says nine a.m., but the project plan says one p.m. to three p.m.", False),
            ("We need a camera to take a group photo.", "We need a camera to take a group photo.", True),
            ("Grandma had two eggs, but Minmin had only soup noodles.", "Minmin has two eggs, but Grandma had only soup noodles.", False),
            ("Reading parents' letters is a tradition at the group birthday party.", "Reading parents' letters is a tradition at the group birthday party.", True),
        ],
        "responses": [
            ("What do you need to take a group photo?", "A camera.|A cake.|An egg.", 0),
            ("What time is the party in the project plan?", "Nine a.m.|One p.m. to three p.m.|Three p.m. to nine p.m.", 1),
            ("What can you give at the planned birthday party?", "Soup noodles.|School buildings.|Birthday cards.", 2),
            ("Which activity shows a birthday tradition in the book?", "Reading parents' letters.|Buying a school building.|Reading a camera.", 0),
            ("What do Minmin's noodles and Grandma's noodles both show?", "They both have two eggs.|They both show love.|They both have tomatoes.", 1),
        ],
        "dialogues": [
            (["Our project plan is for Monday, the twenty-eighth of October.", "The invitation is for the twenty-seventh of October.", "They are different examples."], "Which date is in the project plan?", "The twenty-seventh of October.|The twenty-eighth of October.|The twenty-ninth of October.", 1),
            (["We want to take a group photo.", "Then we need a camera.", "We also need letters for reading."], "What is needed for the photo?", "A camera.|A letter.|An invitation.", 0),
            (["Our party is from one p.m. to three p.m.", "Can we watch a show?", "Yes, and we can give birthday cards."], "Which activity is in their plan?", "Cooking soup.|Playing football.|Giving birthday cards.", 2),
            (["Minmin has two eggs and vegetables in his noodles.", "Grandma had only soup noodles.", "Both bowls show love."], "How are the bowls different?", "Only Grandma has two eggs.|Minmin has eggs and vegetables.|Neither bowl shows love.", 1),
            (["We read our parents' letters at the party.", "Then we say thank you to them.", "It is our birthday tradition."], "What do they do after reading?", "Thank their parents.|Take away the letters.|Cook two eggs.", 0),
        ],
        "passage": "This is the project plan for our group birthday party. It is on Monday, the twenty-eighth of October, from one p.m. to three p.m. We can give birthday cards, read parents' letters, watch a show and take a group photo. We need balloons, birthday hats, gifts, letters and a camera. Reading parents' letters is a tradition. After reading, we say thank you to our parents.",
        "statements": [("The plan is for Monday, the twenty-eighth of October.", True), ("The planned party starts at nine a.m.", False), ("They can read parents' letters and watch a show.", True), ("They do not need a camera.", False), ("They thank their parents after reading the letters.", True)],
        "repeat": ["This is my plan for our group birthday party.", "Our party is on Monday, the twenty-eighth of October, from one p.m. to three p.m.", "We can give birthday cards, read parents' letters and watch a show.", "We need balloons, birthday hats, gifts, letters and a camera.", "It is a tradition to read parents' letters at our group birthday party.", "Minmin has eggs and vegetables, but Grandma had only soup noodles."],
        "qa": [
            ("What do you need for a group photo?", "We need a camera to take a group photo.", "我们需要一部相机来拍集体照。"),
            ("When is the party in the project plan?", "It is on Monday, the twenty-eighth of October.", "它在十月二十八日，星期一。"),
            ("What time is the planned party?", "It is from one p.m. to three p.m.", "它从下午一点到三点。"),
            ("Which two activities can you do in the project plan?", "We can give birthday cards and read parents' letters.", "我们能送生日卡片并读父母的信。"),
            ("What is a tradition at the group birthday party?", "It is a tradition to read parents' letters.", "读父母的信是一项传统。"),
            ("How are Minmin's noodles different from Grandma's?", "Minmin has eggs and vegetables, but Grandma had only soup noodles.", "Minmin有鸡蛋和蔬菜，而奶奶只有汤面。"),
        ],
    },
}


def build(day):
    title, pages, _, difficulty, lmins, smins, plays = META[day]
    data = DATA[day]
    pair = f"4A-T1-W01-D{day:02d}"
    cid = "L" + pair
    def tag(focus, micro=False):
        return (c if micro else a)(pages, focus)
    groups = {
        "words": [word(heard, options.split("|"), ans, tag("听音选词辨别", i == len(data["words"]) - 1)) for i, (heard, options, ans) in enumerate(data["words"])],
        "sentences": [sentence(display, heard, "same" if same else "different", tag("句子信息对应")) for display, heard, same in data["sentences"]],
        "responses": [response(prompt, options.split("|"), ans, tag("听问句选答语", i == 1)) for i, (prompt, options, ans) in enumerate(data["responses"])],
        "dialogues": [dialogue([["f" if i % 2 == 0 else "m", text] for i, text in enumerate(clips)], question, options.split("|"), ans, tag("对话信息整合")) for clips, question, options, ans in data["dialogues"]],
    }
    sections, next_id = [], 1
    for i, (section_id, name, tip, key) in enumerate(SECTION_SPECS):
        section = make_section(section_id, name, tip, plays[i], groups[key], cid, next_id)
        sections.append(section)
        next_id += len(section["questions"])
    passage = make_section("passage", "听短文判断", "先听完整短文，再判断每句话是否正确", plays[4], [passage_statement(statement, correct, tag("短文跨句判断")) for statement, correct in data["statements"]], cid, next_id)
    passage.update(shared_audio=True, passage_audio=f"static/audio/listening/{cid}/p01.mp3", passage_transcript=[["n", data["passage"]]])
    sections.append(passage)
    common = dict(weekly_batch_id=BATCH, study_pack=pair, pair_id=pair, publication_status="formal", week=6, day=day-25, scope=f"4A Unit 4 {pages}", difficulty=difficulty)
    count = sum(len(section["questions"]) for section in sections)
    listening = dict(common, course_id=cid, title=f"四上·第{day}课｜{title}（听力）", course_type="weekly_test" if day == 30 else "training", est_minutes=lmins, scoring={"per_question": 100//count, "total": 100}, test_audio=f"static/audio/listening/{cid}/hello.mp3", test_transcript=[["n", "Hello! Can you hear me? Let us begin."]], sections=sections)
    qs = []
    for text in data["repeat"]:
        qs.append(dict(type="repeat", text=text, tag=tag("教材句型跟读")))
    for i, (question, expected, hint) in enumerate(data["qa"]):
        qs.append(dict(type="qa", question=question, expected=expected, hint=f"用完整句回答：{hint}", tag=tag("引导问答信息对应", i == 0)))
    for i, question in enumerate(qs, 1):
        question.update(id=i, audio=f"static/audio/speaking/S{pair}/q{i:02d}.mp3", parent_note=parent_note(question["tag"]))
    speaking = dict(common, course_id="S"+pair, title=f"四上·第{day}课｜{title}（口语）", course_type="weekly_review" if day == 30 else "training", est_minutes=smins, questions=qs)
    return listening, speaking


def documents(listening, speaking):
    mapping = ["# Unit 4 D26–D30 教材与课程映射", "", "设计依据：D36已批准的五组结构；本批直接沿用成熟题型和增量音频工具。", "", "| 课次 | 配对 ID | 教材范围 | 听力/口语 | 难度 | 约总分钟 |", "|---|---|---|---:|---|---:|"]
    parent = ["# Unit 4 D26–D30 家长版答案、原文与口语目标句", "", "家长专用。以下为依据教材转录自编的听力，不是无音轨 Listen 栏目的原答案。", ""]
    for document in (mapping, parent):
        document[2:2] = ["设计批次：2026-10-13；内容定稿：2026-10-14。", ""]
    for day, lcourse, scourse in zip(META, listening, speaking):
        title, pages, planned, _, lmins, smins, _ = META[day]
        count = sum(len(sec["questions"]) for sec in lcourse["sections"])
        mapping.append(f"| D{day} {title} | {lcourse['pair_id']} | Unit 4 {pages} | {count}/{len(scourse['questions'])} | {planned} | {lmins+smins} |")
        parent += [f"## D{day} {lcourse['course_id']} / {scourse['course_id']}", "", f"教材范围：Unit 4 {pages}。", ""]
        for section in lcourse["sections"]:
            parent += [f"### {section['name']}（最多{section['max_plays']}次）", ""]
            if section.get("shared_audio"):
                parent += ["原文："+section["passage_transcript"][0][1], ""]
            parent += ["| 题号 | 原文/题干 | 答案 | 来源 |", "|---:|---|---|---|"]
            for question in section["questions"]:
                parent.append(f"| {question['id']} | {transcript_text(question)} | {answer_text(question)} | {question['tag']} |")
            parent.append("")
        parent += ["### 口语目标", "", "| 题号 | 类型 | 示范或问句 | 目标答案 | 中文提示 |", "|---:|---|---|---|---|"]
        for question in scourse["questions"]:
            target = question.get("text", question.get("expected"))
            prompt = question.get("text", question.get("question"))
            parent.append(f"| {question['id']} | {question['type']} | {prompt} | {target} | {question.get('hint', '')} |")
        parent.append("")
    notes = ["", "## 事实与练习边界", "", "- 事实源：确认版 B006 p31–38及全册最终文件同页段，已核验无待确认项。未进入 Unit 5 p39及以后。", "- D26仅使用p31–32词汇、活动；D27加入p33邀请；D28加入p34–35来信、感谢与传统；D29加入p36–37故事；D30加入p38计划并综合。", "- p33邀请：27 October / 9 a.m. / Hall, School Building 2；p38计划：Monday, 28 October / 1 p.m.–3 p.m.。两者为不同教材示例，不对应真实学校排期；课程不设置open_date。", "- p35未明确的收信人不猜测；只使用p34明确具名的Minmin与football player，以及明文Shenshen感谢卡。无名图画来信维持无名。", "- 所有Listen听力为依据转录自编；D29最后一个对话为p37句型的自编生日面计划，不声称教材原有事实。", "- 166题：A主线151题、C微调15题；每课2听力C+1口语C，沿用中性听音选词、听问句选答语及信息对应。没有新增formal学情证据，不扩大为约20%弱项，不读private、不从test或单次错误推断弱项。", "- 口语最长18词，现行20秒录音上限不变；QA中文完整句锁定评测目标，儿童副本仅保留可见题干及提示。", "- 难度从直接词汇/活动识别升至时间地点、来信信息、故事前后对比、邀请/计划区分及综合输出；播放次数逐课递减，D30为weekly_test/weekly_review。", "- 父JSON为唯一权威活动课程源，draft仅为派生副本/清单。01本地提交后交00抽查，02再同步发布目录、固定音频SHA、工程回归及Streamlit发布。", "- 01不push、不部署、不改录音/评分/认证/进度或固定发布路由，不产生学习记录。", ""]
    max_words = max(len(question.get("text", question.get("expected")).split()) for course in speaking for question in course["questions"])
    notes = [note.replace("口语最长18词", f"口语最长{max_words}词") for note in notes]
    mapping += notes
    parent += notes
    return "\n".join(mapping), "\n".join(parent)


def main():
    pairs = [build(day) for day in META]
    listening, speaking = map(list, zip(*pairs))
    for module, courses, builder in (("listening", listening, child_listening), ("speaking", speaking, child_speaking)):
        catalog = []
        for course in courses:
            json_write(ROOT / "content" / module / f"{course['course_id']}.json", course)
            child = builder(course)
            json_write(DRAFT / "child" / module / f"{course['course_id']}.json", child)
            catalog.append(child_catalog_entry(course, child))
        json_write(DRAFT / "child" / module / "catalog.json", catalog)
    json_write(DRAFT / "audio-generation-plan.json", audio_plan(listening, speaking))
    json_write(DRAFT / "study-packs.json", dict(weekly_batch_id=BATCH, publication_status="formal", visible=True, authority_note="父JSON为唯一权威源；本目录仅派生副本与计划。", study_packs=[dict(lesson=day, pair_id=lcourse["pair_id"], study_pack=lcourse["study_pack"], textbook_scope=lcourse["scope"], planned_difficulty=META[day][2], listening_course_id=lcourse["course_id"], speaking_course_id=scourse["course_id"]) for day, (lcourse, scourse) in zip(META, pairs)]))
    mapping, parent = documents(listening, speaking)
    PREFIX.parent.mkdir(parents=True, exist_ok=True)
    Path(str(PREFIX)+"教材与课程映射.md").write_text(mapping, encoding="utf-8", newline="\n")
    Path(str(PREFIX)+"家长版答案原文.md").write_text(parent, encoding="utf-8", newline="\n")
    print("Built D26-D30: 110 listening questions, 56 speaking questions, 154 audio targets.")


if __name__ == "__main__":
    main()
