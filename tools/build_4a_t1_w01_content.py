# -*- coding: utf-8 -*-
"""Build the approved 4A T1 W01 content-only draft package.

This script writes the governed draft package. Window 02 promotes the same
approved parent JSON into the single active source with publication_status=test.
"""
from __future__ import annotations

import json
import hashlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BATCH = "4A-T1-W01"
OUT = ROOT / "content" / "drafts" / BATCH
LISTENING_OUT = OUT / "listening"
SPEAKING_OUT = OUT / "speaking"
DOCS_OUT = ROOT / "docs" / "course-batches"
CHILD_LISTENING_OUT = OUT / "child" / "listening"
CHILD_SPEAKING_OUT = OUT / "child" / "speaking"

DAY_META = {
    1: {
        "date": "2026-09-01",
        "weekday": "周二",
        "title": "四上·第1周·周二｜认识新同学·基础",
        "scope": "4A M1U1 p2",
        "json_difficulty": "L1",
        "planned_difficulty": "L1",
        "listening_minutes": 17,
        "speaking_minutes": 8,
        "focus": "姓名、年龄、基础介绍",
    },
    2: {
        "date": "2026-09-02",
        "weekday": "周三",
        "title": "四上·第1周·周三｜介绍朋友·数字与能力",
        "scope": "4A M1U1 p2-p3",
        "json_difficulty": "L1",
        "planned_difficulty": "L1+",
        "listening_minutes": 17,
        "speaking_minutes": 8,
        "focus": "11-16、介绍朋友、能力表达",
    },
    3: {
        "date": "2026-09-03",
        "weekday": "周四",
        "title": "四上·第1周·周四｜人物信息·连续对话",
        "scope": "4A M1U1 p2-p3",
        "json_difficulty": "L2",
        "planned_difficulty": "L2",
        "listening_minutes": 22,
        "speaking_minutes": 8,
        "focus": "连续对话、人物与信息对应",
    },
    4: {
        "date": "2026-09-04",
        "weekday": "周五",
        "title": "四上·第1周·周五｜相似信息辨别",
        "scope": "4A M1U1 p2-p3",
        "json_difficulty": "L2",
        "planned_difficulty": "L2+",
        "listening_minutes": 22,
        "speaking_minutes": 8,
        "focus": "相似干扰项、跨句判断、部分低播放次数",
    },
    5: {
        "date": "2026-09-05",
        "weekday": "周六",
        "title": "四上·第1周·周六｜人物介绍·综合迁移",
        "scope": "4A M1U1 p2-p3",
        "json_difficulty": "L3",
        "planned_difficulty": "L3",
        "listening_minutes": 27,
        "speaking_minutes": 8,
        "focus": "较长人物介绍、跨句提取信息、陌生语境迁移",
    },
    6: {
        "date": "2026-09-06",
        "weekday": "周日",
        "title": "四上·第1周·周日｜M1U1第一周综合",
        "scope": "4A M1U1 p2-p3综合",
        "json_difficulty": "L3",
        "planned_difficulty": "L3综合",
        "listening_minutes": 30,
        "speaking_minutes": 8,
        "focus": "周综合检测、跨题型整合、稳定输出",
    },
}


def a(page: str, focus: str) -> str:
    return f"A主线·{page}·{focus}"


def c(page: str, focus: str) -> str:
    return f"C微调·{page}·{focus}"


def parent_note(tag: str) -> str:
    pages = "p2-p3" if "p2-p3" in tag else ("p3" if "p3" in tag else "p2")
    if tag.startswith("C微调"):
        return f"00确认摘要轻量复测；语言材料仅取教材PDF {pages}，不作未掌握结论"
    return f"教材PDF {pages} 主线或不增加新知识的同语境迁移"


def word(heard, options, answer, tag):
    return {
        "type": "word_choice",
        "tag": tag,
        "parent_note": parent_note(tag),
        "options": options,
        "answer": answer,
        "transcript": [["n", heard]],
    }


def sentence(display, heard, answer, tag):
    return {
        "type": "sentence_judge",
        "tag": tag,
        "parent_note": parent_note(tag),
        "display": display,
        "answer": answer,
        "transcript": [["n", heard]],
    }


def response(prompt, options, answer, tag):
    return {
        "type": "question_response",
        "tag": tag,
        "parent_note": parent_note(tag),
        "options": options,
        "answer": answer,
        "transcript": [["n", prompt]],
    }


def dialogue(clips, question, options, answer, tag):
    return {
        "type": "dialogue_choice",
        "tag": tag,
        "parent_note": parent_note(tag),
        "question_text": question,
        "options": options,
        "answer": answer,
        "transcript": clips + [["n", f"Question: {question}"]],
    }


def passage_statement(statement, answer, tag):
    return {
        "type": "passage_judge",
        "tag": tag,
        "parent_note": parent_note(tag),
        "statement": statement,
        "answer": "true" if answer else "false",
    }


LISTENING_DATA = {
    1: {
        "max_plays": [2, 2, 2, 2, 3],
        "words": [
            word("Sally", ["Sally", "Kitty", "Tracy"], 0, a("p2", "姓名直接识别")),
            word("Paul", ["Peter", "Paul", "Danny"], 1, a("p2", "姓名直接识别")),
            word("sister", ["sister", "brother", "classmate"], 0, a("p2", "人物关系")),
            word("brother", ["classmate", "brother", "sister"], 1, c("p2", "人物信息对应")),
        ],
        "sentences": [
            sentence("This is my sister.", "This is my sister.", "same", a("p2", "基础介绍")),
            sentence("Her name is Sally.", "Her name is Sally.", "same", c("p2", "his-her辨别")),
            sentence("His name is Peter.", "His name is Paul.", "different", c("p2", "his-her与姓名对应")),
            sentence("Kitty is Peter's classmate.", "Kitty is Peter's classmate.", "same", a("p2", "人物关系")),
        ],
        "responses": [
            response("Who is Sally?", ["She's Kitty's sister.", "He's Kitty's brother.", "She's Peter's classmate."], 0, a("p2", "人物关系")),
            response("What's her name?", ["Her name is Sally.", "His name is Paul.", "My name is Kitty."], 0, c("p2", "听问句选答语与her")),
            response("How old is Sally?", ["She's twelve.", "He's six.", "She's nine."], 0, a("p2", "年龄")),
            response("Who is Paul?", ["He's Kitty's brother.", "She's Kitty's sister.", "He's Peter's classmate."], 0, a("p2", "人物关系")),
        ],
        "dialogues": [
            dialogue([["f", "Good morning, Peter."], ["m", "Good morning, Kitty."]], "Who says good morning to Peter?", ["Kitty.", "Sally.", "Paul."], 0, a("p2", "见面问候")),
            dialogue([["f", "This is my sister."], ["f", "Her name is Sally."]], "What is the sister's name?", ["Sally.", "Kitty.", "Tracy."], 0, a("p2", "介绍家人")),
            dialogue([["f", "This is my brother."], ["f", "His name is Paul. He's only six."]], "How old is Paul?", ["Six.", "Twelve.", "Nine."], 0, a("p2", "年龄")),
            dialogue([["f", "My name is Kitty."], ["f", "I'm Peter's classmate."]], "Who is Kitty's classmate?", ["Peter.", "Paul.", "Sally."], 0, a("p2", "人物信息对应")),
        ],
        "passage": "This is Kitty. Sally is her sister. Sally is twelve. Paul is her brother. He is only six. Kitty is Peter's classmate. They are going to the park.",
        "statements": [
            passage_statement("Sally is Kitty's sister.", True, a("p2", "短文取信息")),
            passage_statement("Sally is six.", False, a("p2", "年龄对应")),
            passage_statement("Paul is Kitty's brother.", True, a("p2", "人物关系")),
            passage_statement("Kitty is Paul's classmate.", False, a("p2", "人物对应")),
        ],
    },
    2: {
        "max_plays": [2, 2, 2, 2, 3],
        "words": [
            word("eleven", ["eleven", "twelve", "thirteen"], 0, a("p3", "数字11-16")),
            word("twelve", ["thirteen", "twelve", "fourteen"], 1, a("p3", "数字11-16")),
            word("thirteen", ["fourteen", "fifteen", "thirteen"], 2, a("p3", "数字11-16")),
            word("sixteen", ["six", "sixteen", "fifteen"], 1, c("p3", "听音选词数字辨别")),
        ],
        "sentences": [
            sentence("This is my friend.", "This is my friend.", "same", a("p3", "介绍朋友")),
            sentence("Her name is Danny.", "His name is Danny.", "different", c("p3", "his-her辨别")),
            sentence("Danny is nine.", "Danny is nine.", "same", a("p3", "年龄")),
            sentence("Tracy can ride a bicycle.", "Tracy can skip.", "different", a("p3", "能力表达")),
        ],
        "responses": [
            response("What can Danny do?", ["He can ride a bicycle.", "She can skip.", "He is nine."], 0, a("p3", "能力表达")),
            response("How old is Tracy?", ["She's thirteen.", "He's nine.", "She's twelve."], 0, a("p3", "年龄")),
            response("What's his name?", ["His name is Danny.", "Her name is Tracy.", "My name is Peter."], 0, c("p3", "听问句选答语与his")),
            response("What can she do?", ["She can skip.", "He can ride a bicycle.", "She's thirteen."], 0, a("p3", "能力表达")),
        ],
        "dialogues": [
            dialogue([["f", "This is my friend, Paul."], ["m", "I'm eleven."]], "How old is Paul?", ["Eleven.", "Twelve.", "Thirteen."], 0, a("p2-p3", "同语境数字迁移")),
            dialogue([["f", "This is my friend."], ["f", "His name is Danny. He can ride a bicycle."]], "What can Danny do?", ["Ride a bicycle.", "Skip.", "Go to the park."], 0, a("p3", "介绍朋友与能力")),
            dialogue([["m", "What's her name?"], ["f", "Her name is Tracy. She's thirteen."]], "How old is Tracy?", ["Thirteen.", "Twelve.", "Sixteen."], 0, a("p3", "姓名年龄对应")),
            dialogue([["f", "Danny can ride a bicycle."], ["m", "Tracy can skip."]], "Who can skip?", ["Tracy.", "Danny.", "Peter."], 0, a("p3", "人物能力对应")),
        ],
        "passage": "This is Kitty's friend, Tracy. She's thirteen. She can skip. Danny is Peter's friend. He's nine. He can ride a bicycle.",
        "statements": [
            passage_statement("Tracy is Kitty's friend.", True, a("p2-p3", "人物关系迁移")),
            passage_statement("Danny is Kitty's friend.", False, c("p2-p3", "人物信息对应")),
            passage_statement("Tracy can skip.", True, a("p3", "能力")),
            passage_statement("Danny can skip.", False, a("p3", "能力对应")),
        ],
    },
    3: {
        "max_plays": [2, 2, 2, 2, 3],
        "words": [
            word("fourteen", ["thirteen", "fourteen", "fifteen"], 1, a("p3", "相邻数字")),
            word("fifteen", ["fifteen", "sixteen", "fourteen"], 0, a("p3", "相邻数字")),
            word("her", ["his", "her", "my"], 1, c("p2-p3", "his-her-your相关辨别")),
            word("ride a bicycle", ["ride a bicycle", "skip", "go to the park"], 0, a("p3", "能力短语")),
        ],
        "sentences": [
            sentence("Peter's friend is Danny.", "Peter's friend is Danny.", "same", a("p2-p3", "人物关系迁移")),
            sentence("Sally is six and Paul is twelve.", "Sally is twelve and Paul is six.", "different", a("p2", "跨句年龄对应")),
            sentence("Danny is nine and he can ride a bicycle.", "Danny is nine and he can ride a bicycle.", "same", a("p3", "年龄能力整合")),
            sentence("His name is Tracy and he can skip.", "Her name is Tracy and she can skip.", "different", c("p3", "人物代词信息对应")),
        ],
        "responses": [
            response("Who is she?", ["She's Kitty's sister, Sally.", "He's Kitty's brother, Paul.", "She's Peter's friend, Danny."], 0, a("p2", "人物关系")),
            response("How old is Peter's friend Danny?", ["He's nine.", "She's thirteen.", "He's six."], 0, a("p3", "连续信息")),
            response("What can Tracy do?", ["She can skip.", "He can ride a bicycle.", "She's thirteen."], 0, a("p3", "能力")),
            response("What's her name?", ["Her name is Tracy.", "His name is Danny.", "Her name is Sally."], 0, c("p2-p3", "听问句选答语与人物对应")),
        ],
        "dialogues": [
            dialogue([["f", "This is my friend."], ["f", "His name is Danny."], ["m", "I'm nine."]], "How old is Danny?", ["Nine.", "Twelve.", "Thirteen."], 0, a("p3", "连续对话")),
            dialogue([["m", "Is Sally Kitty's sister?"], ["f", "Yes. Sally is twelve."], ["m", "Paul is her brother. He's six."]], "Who is six?", ["Paul.", "Sally.", "Kitty."], 0, a("p2", "连续对话年龄对应")),
            dialogue([["f", "This is Tracy."], ["m", "How old is she?"], ["f", "She's thirteen, and she can skip."]], "What can Tracy do?", ["Skip.", "Ride a bicycle.", "Go to the park."], 0, a("p3", "连续对话能力")),
            dialogue([["m", "Danny can ride a bicycle."], ["f", "Tracy can skip."], ["m", "They are friends."]], "Who can ride a bicycle?", ["Danny.", "Tracy.", "Sally."], 0, a("p3", "人物能力对应")),
        ],
        "passage": "Kitty is Peter's classmate. Sally is Kitty's sister, and she's twelve. Paul is Kitty's brother, and he's six. Peter's friend Danny is nine and can ride a bicycle. Tracy is thirteen and can skip.",
        "statements": [
            passage_statement("Kitty is Peter's classmate.", True, a("p2", "人物关系")),
            passage_statement("Sally is six.", False, c("p2", "数字与人物对应")),
            passage_statement("Danny can ride a bicycle.", True, a("p3", "能力")),
            passage_statement("Tracy is twelve.", False, a("p3", "跨句年龄")),
        ],
    },
    4: {
        "max_plays": [1, 2, 1, 2, 3],
        "words": [
            word("thirteen", ["thirteen", "fourteen", "fifteen"], 0, a("p3", "相似数字干扰")),
            word("fourteen", ["fifteen", "fourteen", "sixteen"], 1, a("p3", "相似数字干扰")),
            word("fifteen", ["fourteen", "sixteen", "fifteen"], 2, a("p3", "相似数字干扰")),
            word("her", ["his", "my", "her"], 2, a("p2-p3", "物主词")),
            word("sixteen", ["six", "sixteen", "thirteen"], 1, c("p3", "听音选词数字辨别")),
        ],
        "sentences": [
            sentence("Paul is twelve.", "Sally is twelve, but Paul is six.", "different", a("p2", "跨句人物年龄")),
            sentence("Kitty is Peter's classmate.", "Kitty is Peter's classmate, and Sally is Kitty's sister.", "same", a("p2", "主句信息判断")),
            sentence("Danny can skip.", "Danny is nine, and he can ride a bicycle.", "different", a("p3", "跨句能力判断")),
            sentence("Tracy is thirteen and she can skip.", "Tracy is thirteen, and she can skip.", "same", a("p3", "双信息判断")),
            sentence("His name is Danny.", "Her name is Tracy, and his name is Danny.", "same", c("p3", "his-her跨句辨别")),
        ],
        "responses": [
            response("What's her name?", ["Her name is Tracy.", "His name is Danny.", "Her name is Sally."], 0, c("p2-p3", "听问句选答语与人物对应")),
            response("How old is the girl who can skip?", ["She's thirteen.", "He's nine.", "She's twelve."], 0, a("p3", "跨信息问答")),
            response("What can Peter's friend Danny do?", ["He can ride a bicycle.", "She can skip.", "He's nine."], 0, a("p3", "跨信息问答")),
            response("Who is Kitty's brother?", ["Paul.", "Peter.", "Danny."], 0, a("p2", "人物关系")),
            response("How old is Kitty's sister?", ["She's twelve.", "He's six.", "She's thirteen."], 0, a("p2", "人物年龄")),
        ],
        "dialogues": [
            dialogue([["f", "This is my friend Danny."], ["m", "I'm nine."], ["f", "He can ride a bicycle."], ["m", "Yes, I can."]], "What can Danny do?", ["Ride a bicycle.", "Skip.", "Go to the park."], 0, a("p3", "连续对话")),
            dialogue([["m", "Is Tracy twelve?"], ["f", "No. She's thirteen."], ["m", "Can she skip?"], ["f", "Yes, she can."]], "How old is Tracy?", ["Thirteen.", "Twelve.", "Sixteen."], 0, c("p3", "数字与人物信息对应")),
            dialogue([["f", "Sally is Kitty's sister."], ["m", "She's twelve."], ["f", "Paul is Kitty's brother."], ["m", "He's only six."]], "Who is twelve?", ["Sally.", "Paul.", "Kitty."], 0, a("p2", "跨句人物年龄")),
            dialogue([["m", "Danny is my friend."], ["f", "Tracy is my friend too."], ["m", "Danny can ride a bicycle."], ["f", "Tracy can skip."]], "Who can skip?", ["Tracy.", "Danny.", "Peter."], 0, a("p3", "跨句人物能力")),
            dialogue([["f", "Good morning, Peter."], ["m", "Good morning, Kitty."], ["f", "We are going to the park."], ["m", "See you."]], "Where are Peter and Kitty going?", ["To the park.", "To meet Tracy.", "To ride a bicycle."], 0, a("p2", "连续对话地点")),
        ],
        "passage": "Peter and Kitty are classmates. Kitty's sister is Sally. Sally is twelve. Kitty's brother is Paul, and he's only six. Danny is Peter's friend. He's nine and can ride a bicycle. Tracy is Kitty's friend. She's thirteen and can skip.",
        "statements": [
            passage_statement("Peter and Kitty are classmates.", True, a("p2", "人物关系")),
            passage_statement("Paul is twelve.", False, a("p2", "人物年龄")),
            passage_statement("Danny is Kitty's friend.", False, a("p2-p3", "人物对应")),
            passage_statement("Tracy is thirteen.", True, c("p3", "数字信息辨别")),
            passage_statement("Danny can ride a bicycle.", True, a("p3", "能力")),
        ],
    },
    5: {
        "max_plays": [1, 1, 2, 2, 3],
        "words": [
            word("fourteen", ["thirteen", "fourteen", "fifteen"], 1, a("p3", "相邻数字")),
            word("sixteen", ["six", "sixteen", "fifteen"], 1, c("p3", "听音选词数字辨别")),
            word("ride a bicycle", ["ride a bicycle", "skip", "go to the park"], 0, a("p3", "能力短语")),
            word("his", ["her", "his", "my"], 1, a("p2-p3", "物主词")),
            word("classmate", ["classmate", "brother", "friend"], 0, a("p2", "人物关系")),
        ],
        "sentences": [
            sentence("Sally is Kitty's sister, and she's twelve.", "Sally is Kitty's sister, and she's twelve.", "same", a("p2", "复合信息")),
            sentence("Paul is Peter's brother, and he's six.", "Paul is Kitty's brother, and he's six.", "different", c("p2", "人物信息对应")),
            sentence("Danny is thirteen and can skip.", "Danny is nine and can ride a bicycle.", "different", a("p3", "双信息辨别")),
            sentence("Tracy is thirteen and can skip.", "Tracy is thirteen and can skip.", "same", a("p3", "双信息辨别")),
            sentence("Kitty and Peter are going to the park.", "Peter and Kitty are going to the park.", "same", a("p2", "语序迁移")),
        ],
        "responses": [
            response("Who is twelve?", ["Sally.", "Tracy.", "Kitty."], 0, a("p2", "跨信息问答")),
            response("What's his name, and what can he do?", ["His name is Danny, and he can ride a bicycle.", "Her name is Tracy, and she can skip.", "His name is Paul, and he's six."], 0, c("p3", "听问句选答语与信息整合")),
            response("Who is Kitty's brother, and how old is he?", ["Paul. He's six.", "Peter. He's nine.", "Danny. He's thirteen."], 0, a("p2", "人物年龄整合")),
            response("How old is the friend who can skip?", ["She's thirteen.", "He's nine.", "She's twelve."], 0, a("p3", "跨句年龄能力")),
            response("Danny is nine. What can he do?", ["He can ride a bicycle.", "She can skip.", "He can go to the park."], 0, a("p3", "跨句年龄能力")),
        ],
        "dialogues": [
            dialogue([["f", "This is my friend Danny."], ["m", "I'm nine."], ["f", "He can ride a bicycle."], ["m", "Yes, I can."]], "How old is Danny, and what can he do?", ["He's nine and can ride a bicycle.", "He's six and is going to the park.", "She's thirteen and can skip."], 0, a("p2-p3", "陌生语境迁移")),
            dialogue([["m", "This is Tracy."], ["f", "I'm thirteen."], ["m", "She can skip."], ["f", "Yes, I can."]], "Who is thirteen?", ["Tracy.", "Danny.", "Sally."], 0, c("p3", "人物与数字对应")),
            dialogue([["f", "Sally is Kitty's sister."], ["m", "Paul is Kitty's brother."], ["f", "Sally is twelve."], ["m", "Paul is six."]], "How old is Kitty's brother?", ["Six.", "Twelve.", "Thirteen."], 0, a("p2", "长对话取信息")),
            dialogue([["m", "Peter, this is my friend Tracy."], ["f", "She's thirteen and can skip."], ["m", "My friend Danny is nine."], ["f", "He can ride a bicycle."]], "What can Peter's friend do?", ["Ride a bicycle.", "Skip.", "Go to the park."], 0, a("p3", "跨句人物能力")),
            dialogue([["f", "Good morning, Kitty."], ["m", "Good morning, Peter."], ["f", "This is Sally and this is Paul."], ["m", "Hi, Sally. Hi, Paul."], ["f", "We are going to the park."]], "Who is going to the park?", ["Peter, Kitty, Sally and Paul.", "Danny and Tracy.", "Only Peter and Paul."], 0, a("p2", "长对话整合")),
        ],
        "passage": "Sally is Kitty's sister. She's twelve. Paul is Kitty's brother, and he's only six. Danny is Peter's friend. He's nine and can ride a bicycle. Tracy is Kitty's friend. She's thirteen and can skip. Peter and Kitty are classmates.",
        "statements": [
            passage_statement("Sally, Paul, Danny and Tracy are in the passage.", True, a("p2-p3", "陌生语境迁移")),
            passage_statement("Sally is Kitty's sister, and she's six.", False, a("p2", "跨句人物年龄")),
            passage_statement("Danny is Peter's friend.", True, c("p2-p3", "人物信息对应")),
            passage_statement("Tracy can ride a bicycle.", False, a("p3", "人物能力")),
            passage_statement("Peter and Kitty are classmates.", True, a("p2", "人物关系")),
        ],
    },
    6: {
        "max_plays": [1, 1, 1, 2, 3],
        "words": [
            word("fifteen", ["fourteen", "fifteen", "sixteen"], 1, a("p3", "周综合数字")),
            word("thirteen", ["thirteen", "fourteen", "twelve"], 0, c("p3", "听音选词数字辨别")),
            word("brother", ["classmate", "brother", "friend"], 1, a("p2", "人物关系")),
            word("ride a bicycle", ["skip", "ride a bicycle", "go to the park"], 1, a("p3", "能力短语")),
            word("her", ["his", "my", "her"], 2, a("p2-p3", "物主词")),
        ],
        "sentences": [
            sentence("Paul is Kitty's brother, and he's only six.", "Paul is Kitty's brother, and he's only six.", "same", a("p2", "周综合人物年龄")),
            sentence("Tracy is twelve and can ride a bicycle.", "Tracy is thirteen and can skip.", "different", c("p3", "数字与人物能力对应")),
            sentence("Danny is Peter's friend, and he can ride a bicycle.", "Danny is Peter's friend, and he can ride a bicycle.", "same", a("p3", "复合信息")),
            sentence("Sally is Peter's classmate.", "Sally is Kitty's sister, and Kitty is Peter's classmate.", "different", a("p2", "跨句人物关系")),
            sentence("Peter and Kitty are going to the park.", "Kitty and Peter are going to the park.", "same", a("p2", "同义语序")),
        ],
        "responses": [
            response("What's her name, and how old is she?", ["Her name is Tracy, and she's thirteen.", "His name is Danny, and he's nine.", "Her name is Sally, and she's six."], 0, c("p2-p3", "听问句选答语与跨句整合")),
            response("Who can ride a bicycle?", ["Danny can.", "Tracy can.", "Sally can."], 0, a("p3", "人物能力")),
            response("Who is Kitty's sister, and how old is she?", ["Sally. She's twelve.", "Tracy. She's thirteen.", "Kitty. She's nine."], 0, a("p2", "人物年龄关系")),
            response("Tracy is thirteen. What can she do?", ["She can skip.", "He can ride a bicycle.", "She can go to the park."], 0, a("p3", "年龄能力整合")),
            response("Who is Peter's classmate?", ["Kitty.", "Paul.", "Danny."], 0, a("p2", "人物关系")),
        ],
        "dialogues": [
            dialogue([["f", "This is my sister Sally."], ["m", "How old is she?"], ["f", "She's twelve."], ["m", "And Paul?"], ["f", "He's my brother. He's six."]], "Who is six?", ["Paul.", "Sally.", "Kitty."], 0, a("p2", "周综合连续对话")),
            dialogue([["m", "My friend Danny is nine."], ["f", "Can he skip?"], ["m", "No. He can ride a bicycle."], ["f", "Tracy can skip. She's thirteen."]], "Who can skip?", ["Tracy.", "Danny.", "Peter."], 0, c("p3", "人物信息对应")),
            dialogue([["f", "Good morning, Peter."], ["m", "Good morning, Kitty."], ["f", "This is my sister Sally and my brother Paul."], ["m", "Hello, Sally. Hello, Paul."]], "Who says, This is my sister Sally?", ["Kitty.", "Peter.", "Danny."], 0, a("p2", "周综合见面介绍")),
            dialogue([["m", "Peter and Kitty are classmates."], ["f", "Danny is Peter's friend."], ["m", "Tracy is Kitty's friend."], ["f", "Danny can ride a bicycle, and Tracy can skip."]], "Which statement is correct?", ["Danny can ride a bicycle.", "Tracy can ride a bicycle.", "Kitty can skip."], 0, a("p2-p3", "跨句综合")),
            dialogue([["f", "Sally is twelve."], ["m", "Tracy is thirteen."], ["f", "Danny is nine."], ["m", "Paul is only six."]], "Who is thirteen?", ["Tracy.", "Sally.", "Danny."], 0, a("p2-p3", "数字整合")),
        ],
        "passage": "Peter and Kitty are going to the park. Sally is Kitty's sister, and Paul is Kitty's brother. Sally is twelve, and Paul is only six. Danny is Peter's friend. Danny is nine and can ride a bicycle. Tracy is Kitty's friend. Tracy is thirteen and can skip. Peter and Kitty are classmates.",
        "statements": [
            passage_statement("Peter and Kitty are going to the park.", True, a("p2", "周综合场景")),
            passage_statement("Sally is six.", False, a("p2", "跨句数字对应")),
            passage_statement("Danny is Peter's friend.", True, a("p2-p3", "人物对应")),
            passage_statement("Tracy is thirteen and can skip.", True, c("p3", "数字人物能力对应")),
            passage_statement("Peter and Tracy are classmates.", False, a("p2-p3", "跨句人物关系")),
        ],
    },
}


SPEAKING_DATA = {
    1: [
        ("repeat", "Good morning, Peter.", None, None, a("p2", "基础问候")),
        ("repeat", "Good morning, Kitty.", None, None, a("p2", "基础问候")),
        ("repeat", "This is my sister.", None, None, a("p2", "介绍家人")),
        ("repeat", "Her name is Sally.", None, None, c("p2", "his-her稳定输出")),
        ("repeat", "This is my brother.", None, None, a("p2", "介绍家人")),
        ("repeat", "His name is Paul.", None, None, a("p2", "介绍家人")),
        ("qa", "What's her name?", "Her name is Sally.", "用英语说：她的名字叫 Sally。", a("p2", "固定答案问答")),
        ("qa", "How old is Sally?", "She's twelve.", "用英语说：她十二岁。", a("p2", "固定答案问答")),
    ],
    2: [
        ("repeat", "Eleven, twelve, thirteen.", None, None, a("p3", "数字11-13")),
        ("repeat", "Fourteen, fifteen, sixteen.", None, None, a("p3", "数字14-16")),
        ("repeat", "This is my friend.", None, None, a("p3", "介绍朋友")),
        ("repeat", "His name is Danny.", None, None, c("p3", "his-her稳定输出")),
        ("repeat", "He can ride a bicycle.", None, None, a("p3", "能力表达")),
        ("repeat", "She can skip.", None, None, a("p3", "能力表达")),
        ("qa", "What's her name?", "Her name is Tracy.", "用英语说：她的名字叫 Tracy。", a("p3", "固定答案问答")),
        ("qa", "How old is Tracy?", "She's thirteen.", "用英语说：她十三岁。", a("p3", "固定答案问答")),
    ],
    3: [
        ("repeat", "This is my friend. His name is Danny.", None, None, a("p3", "双句介绍")),
        ("repeat", "He's nine. He can ride a bicycle.", None, None, a("p3", "年龄能力整合")),
        ("repeat", "This is my friend. Her name is Tracy.", None, None, a("p3", "双句介绍")),
        ("repeat", "She's thirteen. She can skip.", None, None, a("p3", "年龄能力整合")),
        ("repeat", "Sally is Kitty's sister. She's twelve.", None, None, a("p2", "人物年龄整合")),
        ("repeat", "Paul is Kitty's brother. He's only six.", None, None, c("p2", "人物信息对应")),
        ("qa", "What can Danny do?", "He can ride a bicycle.", "用英语说：他会骑自行车。", a("p3", "自主问答")),
        ("qa", "What can Tracy do?", "She can skip.", "用英语说：她会跳绳。", a("p3", "自主问答")),
    ],
    4: [
        ("repeat", "Kitty is Peter's classmate.", None, None, a("p2", "人物关系迁移")),
        ("repeat", "Sally is Kitty's sister, and she's twelve.", None, None, a("p2", "复合句")),
        ("repeat", "Paul is Kitty's brother, and he's only six.", None, None, a("p2", "复合句")),
        ("repeat", "Danny is nine, and he can ride a bicycle.", None, None, a("p3", "复合句")),
        ("repeat", "Tracy is thirteen, and she can skip.", None, None, a("p3", "复合句")),
        ("repeat", "This is my friend. His name is Danny.", None, None, c("p3", "his-her稳定输出")),
        ("qa", "What can Peter's friend Danny do?", "He can ride a bicycle.", "用英语说：他会骑自行车。", a("p3", "人物信息问答")),
        ("qa", "What can Kitty's friend Tracy do?", "She can skip.", "用英语说：她会跳绳。", a("p3", "人物信息问答")),
    ],
    5: [
        ("repeat", "Good morning. My name is Kitty, and I'm Peter's classmate.", None, None, a("p2", "较长自我介绍")),
        ("repeat", "This is my sister, Sally. She's twelve.", None, None, a("p2", "较长人物介绍")),
        ("repeat", "This is my brother, Paul. He's only six.", None, None, a("p2", "较长人物介绍")),
        ("repeat", "This is my friend, Danny. He's nine, and he can ride a bicycle.", None, None, a("p3", "三信息介绍")),
        ("repeat", "This is my friend, Tracy. She's thirteen, and she can skip.", None, None, a("p3", "三信息介绍")),
        ("repeat", "Her name is Tracy, and his name is Danny.", None, None, c("p3", "his-her稳定输出")),
        ("qa", "Tell me about Danny.", "His name is Danny. He's nine, and he can ride a bicycle.", "用英语说：他叫 Danny，九岁，会骑自行车。", a("p3", "陌生提示综合输出")),
        ("qa", "Tell me about Tracy.", "Her name is Tracy. She's thirteen, and she can skip.", "用英语说：她叫 Tracy，十三岁，会跳绳。", a("p3", "陌生提示综合输出")),
    ],
    6: [
        ("repeat", "Peter and Kitty are classmates, and they are going to the park.", None, None, a("p2", "周综合稳定输出")),
        ("repeat", "Sally is Kitty's sister. She's twelve.", None, None, a("p2", "周综合人物介绍")),
        ("repeat", "Paul is Kitty's brother. He's only six.", None, None, a("p2", "周综合人物介绍")),
        ("repeat", "Danny is Peter's friend. He's nine and can ride a bicycle.", None, None, a("p3", "周综合人物介绍")),
        ("repeat", "Tracy is Kitty's friend. She's thirteen and can skip.", None, None, a("p3", "周综合人物介绍")),
        ("repeat", "His name is Danny, and her name is Tracy.", None, None, c("p3", "his-her稳定输出")),
        ("qa", "Tell me about Danny.", "This is Danny. He's nine, and he can ride a bicycle.", "用英语说：这是 Danny，他九岁，会骑自行车。", a("p3", "综合自主输出")),
        ("qa", "Tell me about Tracy.", "This is Tracy. She's thirteen, and she can skip.", "用英语说：这是 Tracy，她十三岁，会跳绳。", a("p3", "综合自主输出")),
    ],
}


def make_section(section_id, name, tip, max_plays, questions, course_id, start_id):
    built = []
    for offset, source in enumerate(questions):
        question = dict(source)
        question["id"] = start_id + offset
        if question["type"] != "passage_judge":
            question["audio"] = f"static/audio/listening/{course_id}/q{question['id']:02d}.mp3"
        built.append(question)
    return {
        "id": section_id,
        "name": name,
        "tip": tip,
        "max_plays": max_plays,
        "questions": built,
    }


def build_listening(day):
    meta = DAY_META[day]
    data = LISTENING_DATA[day]
    course_id = f"L4A-T1-W01-D{day:02d}"
    pair_id = f"4A-T1-W01-D{day:02d}"
    count = sum(len(data[key]) for key in ("words", "sentences", "responses", "dialogues", "statements"))
    per_section = count // 5
    sections = []
    start = 1
    specs = [
        ("word_discrimination", "听音选词", "听录音，选出你听到的单词或短语", data["words"]),
        ("sentence_meaning", "听句判断", "听句子，判断和屏幕信息是否一致", data["sentences"]),
        ("question_response", "听问句选答语", "听问句，选出最合适的回答", data["responses"]),
        ("dialogue", "听对话选答案", "听连续对话和问题，选出正确答案", data["dialogues"]),
    ]
    for index, (section_id, name, tip, questions) in enumerate(specs):
        section = make_section(section_id, name, tip, data["max_plays"][index], questions, course_id, start)
        sections.append(section)
        start += len(questions)
    passage = make_section(
        "passage",
        "听短文判断",
        "先听完整短文，再判断每句话是否正确",
        data["max_plays"][4],
        data["statements"],
        course_id,
        start,
    )
    passage["shared_audio"] = True
    passage["passage_audio"] = f"static/audio/listening/{course_id}/p01.mp3"
    passage["passage_transcript"] = [["n", data["passage"]]]
    sections.append(passage)
    assert all(len(section["questions"]) == per_section for section in sections)
    return {
        "course_id": course_id,
        "weekly_batch_id": BATCH,
        "study_pack": pair_id,
        "pair_id": pair_id,
        "publication_status": "test",
        "title": meta["title"] + "（听力）",
        "week": 1,
        "day": day,
        "course_type": "weekly_test" if day == 6 else "training",
        "est_minutes": meta["listening_minutes"],
        "scope": meta["scope"],
        "difficulty": meta["json_difficulty"],
        "scoring": {"per_question": 5 if count == 20 else 4, "total": 100},
        "test_audio": f"static/audio/listening/{course_id}/hello.mp3",
        "test_transcript": [["n", "Hello! Can you hear me? Let's begin."]],
        "sections": sections,
    }


def build_speaking(day):
    meta = DAY_META[day]
    course_id = f"S4A-T1-W01-D{day:02d}"
    pair_id = f"4A-T1-W01-D{day:02d}"
    questions = []
    for index, (kind, prompt, expected, hint, tag) in enumerate(SPEAKING_DATA[day], 1):
        question = {
            "id": index,
            "type": kind,
            "audio": f"static/audio/speaking/{course_id}/q{index:02d}.mp3",
            "tag": tag,
            "parent_note": parent_note(tag),
        }
        if kind == "repeat":
            question["text"] = prompt
        else:
            question.update({"question": prompt, "expected": expected, "hint": hint})
        questions.append(question)
    return {
        "course_id": course_id,
        "weekly_batch_id": BATCH,
        "study_pack": pair_id,
        "pair_id": pair_id,
        "publication_status": "test",
        "title": meta["title"] + "（口语）",
        "week": 1,
        "day": day,
        "course_type": "weekly_review" if day == 6 else "training",
        "est_minutes": meta["speaking_minutes"],
        "scope": meta["scope"],
        "difficulty": meta["json_difficulty"],
        "questions": questions,
    }


def json_write(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def listening_version(course):
    raw = (json.dumps(course, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:16]


def speaking_version(course):
    compact = json.dumps(course, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(compact).hexdigest()[:16]


def child_listening(course):
    def asset(value):
        return value.removeprefix("static/")

    return {
        "course_id": course["course_id"],
        "pair_id": course["pair_id"],
        "study_pack": course["study_pack"],
        "course_version": listening_version(course),
        "title": course["title"],
        "week": course["week"],
        "day": course["day"],
        "course_type": course["course_type"],
        "est_minutes": course["est_minutes"],
        "test_audio_asset": asset(course["test_audio"]),
        "sections": [
            {
                "id": section["id"],
                "name": section["name"],
                "tip": section["tip"],
                "max_plays": section["max_plays"],
                **({"shared_audio": True, "passage_audio_asset": asset(section["passage_audio"])} if section.get("shared_audio") else {}),
                "questions": [
                    {
                        "id": question["id"],
                        "type": question["type"],
                        **({"options": question["options"]} if question.get("options") else {}),
                        **({"display": question["display"]} if question.get("display") else {}),
                        **({"statement": question["statement"]} if question.get("statement") else {}),
                        **({"question_text": question["question_text"]} if question.get("question_text") else {}),
                        **({"audio_asset": asset(question["audio"])} if question.get("audio") else {}),
                    }
                    for question in section["questions"]
                ],
            }
            for section in course["sections"]
        ],
    }


def child_speaking(course):
    return {
        "course_id": course["course_id"],
        "pair_id": course["pair_id"],
        "study_pack": course["study_pack"],
        "course_version": speaking_version(course),
        "title": course["title"],
        "week": course["week"],
        "day": course["day"],
        "course_type": course["course_type"],
        "est_minutes": course["est_minutes"],
        "questions": [
            {
                "id": question["id"],
                "type": question["type"],
                **({"text": question["text"]} if question["type"] == "repeat" else {"hint": question["hint"]}),
                "audio_asset": question["audio"].removeprefix("static/"),
            }
            for question in course["questions"]
        ],
    }


def answer_text(question):
    answer = question["answer"]
    if isinstance(answer, int):
        return question["options"][answer]
    return {"same": "一致", "different": "不一致", "true": "正确", "false": "错误"}[answer]


def transcript_text(question):
    if question["type"] == "passage_judge":
        return f"判断：{question['statement']}（原文见本部分短文）"
    heard = " / ".join(text for _, text in question["transcript"])
    if question["type"] == "sentence_judge":
        return f"听到：{heard}；屏显：{question['display']}"
    return heard


def build_audio_plan(listening_courses, speaking_courses):
    items = []
    for course in listening_courses:
        items.append({
            "module": "listening",
            "course_id": course["course_id"],
            "kind": "test_audio",
            "path": course["test_audio"],
            "clips": course["test_transcript"],
        })
        for section in course["sections"]:
            if section.get("shared_audio"):
                items.append({
                    "module": "listening",
                    "course_id": course["course_id"],
                    "kind": "passage",
                    "path": section["passage_audio"],
                    "clips": section["passage_transcript"],
                })
            for question in section["questions"]:
                if question.get("audio"):
                    items.append({
                        "module": "listening",
                        "course_id": course["course_id"],
                        "kind": f"question_{question['id']:02d}",
                        "path": question["audio"],
                        "clips": question["transcript"],
                    })
    for course in speaking_courses:
        for question in course["questions"]:
            spoken = question["text"] if question["type"] == "repeat" else question["question"]
            items.append({
                "module": "speaking",
                "course_id": course["course_id"],
                "kind": f"question_{question['id']:02d}_{question['type']}",
                "path": question["audio"],
                "clips": [["n", spoken]],
            })
    return {
        "weekly_batch_id": BATCH,
        "generation_status": "READY_TO_GENERATE",
        "reason": "02兼容层已允许新旧编号并保持新课程为test；音频生成后仍不得直接开放formal。",
        "expected_listening_outputs": 120,
        "expected_speaking_outputs": 48,
        "expected_total_outputs": 168,
        "after_02_compat_commands": [
            "python tools/make_audio_v2.py L4A-T1-W01-D01 ... D06（兼容后逐课）",
            "python tools/make_audio_speaking.py S4A-T1-W01-D01 ... D06（兼容后逐课）",
            "node tools/sync-p3-assets.mjs",
        ],
        "items": items,
    }


def build_study_packs(listening_courses, speaking_courses):
    packs = []
    for day, (listening, speaking) in enumerate(zip(listening_courses, speaking_courses), 1):
        meta = DAY_META[day]
        packs.append({
            "study_pack": listening["study_pack"],
            "pair_id": listening["pair_id"],
            "date": meta["date"],
            "weekday": meta["weekday"],
            "planned_title": meta["title"],
            "textbook_scope": meta["scope"],
            "planned_difficulty": meta["planned_difficulty"],
            "json_difficulty": meta["json_difficulty"],
            "planned_total_minutes": meta["listening_minutes"] + meta["speaking_minutes"],
            "focus": meta["focus"],
            "listening_course_id": listening["course_id"],
            "speaking_course_id": speaking["course_id"],
            "publication_gate": "须由00按学校当天实际已教范围确认；制作完成不等于正式开放",
        })
    return {
        "weekly_batch_id": BATCH,
        "publication_status": "READY_FOR_TEST",
        "publication_note": "本包可同步到唯一活动课程源，但publication_status保持test，不会进入formal推荐或正式学习记录。",
        "study_packs": packs,
    }


def build_mapping_doc(listening_courses, speaking_courses):
    lines = [
        "# 4A T1 W01 六日教材与课程映射",
        "",
        "> 状态：`BLOCKED_BY_ID_COMPAT`。本文件只记录内容与教材映射；课程未进入活动目录、未部署、未开放 formal。",
        "",
        "## 教材事实边界",
        "",
        "- 实际视觉核对教材 PDF：课本 p2 对应 PDF 第7页，p3 对应 PDF 第8页。",
        "- p2：Peter/Kitty/Sally/Paul、sister/brother、twelve/six、classmate、park、Good morning/Goodbye/See you。",
        "- p3：eleven-sixteen、Danny/Tracy、friend、age、ride a bicycle、skip。",
        "- 明确排除 p4-p6：student number、Jill、新同学课堂、自述短文、like+V-ing、desk/mask 与姓名拼写等。",
        "",
        "## 六日映射",
        "",
        "| 日次 | 日期 | study pack / pair | 听力 | 口语 | 页段 | 难度 | 题量 | 总时长 | 重点 |",
        "|---|---|---|---|---|---|---|---:|---:|---|",
    ]
    for day, (listening, speaking) in enumerate(zip(listening_courses, speaking_courses), 1):
        meta = DAY_META[day]
        lines.append(
            f"| D{day:02d} {meta['weekday']} | {meta['date'][5:]} | {listening['pair_id']} | "
            f"{listening['course_id']} | {speaking['course_id']} | {meta['scope']} | {meta['planned_difficulty']} "
            f"(JSON {meta['json_difficulty']}) | {sum(len(s['questions']) for s in listening['sections'])}+8 | "
            f"约{meta['listening_minutes'] + meta['speaking_minutes']}分钟 | {meta['focus']} |"
        )
    lines.extend([
        "",
        "## A主线与C微调",
        "",
        "- A主线：教材 p2-p3 原句、原人物/数字/能力，以及不增加新知识的同语境重组。",
        "- C微调：每门课最多20%，只轻量复测听问句选答语、听音选词、his/her、人物信息对应和数字辨别。",
        "- W01D46 仅有80分摘要且无逐题证据，本批未据此新增任何弱项。",
        "- `test` 数据、单次错误与 p4-p6 旧坑均未用于本批。",
        "",
        "## 难度如何实际上升",
        "",
        "- D01：单句、直接识别，所有部分至少2次播放。",
        "- D02：加入11-16、介绍朋友与能力的双信息组合。",
        "- D03：对话增加到三轮，要求人物-年龄-能力对应。",
        "- D04：25题；听音选词与听问句选答语降为1次，加入相似数字和跨句判断。",
        "- D05：25题；部分单句1次，人物介绍更长，问答需要整合姓名、年龄与能力。",
        "- D06：25题周综合；前三类短音频1次，长对话2次、短文3次，避免限次导致长材料失真。",
        "",
        "## 发布边界",
        "",
        "D01-D06 即使内容完成，也必须由00根据学校当天实际已教范围决定是否开放；本内容提交不含部署或可见性变更。",
        "",
    ])
    return "\n".join(lines)


def build_parent_doc(listening_courses, speaking_courses):
    lines = [
        "# 4A T1 W01 家长版答案、原文与口语目标句",
        "",
        "> 家长专用内容。不得直接作为儿童公开副本。课程当前为 `BLOCKED_BY_ID_COMPAT` 内容草案。",
        "",
    ]
    for day, (listening, speaking) in enumerate(zip(listening_courses, speaking_courses), 1):
        meta = DAY_META[day]
        lines.extend([
            f"## D{day:02d} {meta['weekday']}｜{meta['title']}",
            "",
            f"- 教材：{meta['scope']}；计划难度：{meta['planned_difficulty']}；听力 {sum(len(s['questions']) for s in listening['sections'])} 题，口语 8 题。",
            "",
            "### 听力答案与原文",
            "",
        ])
        for section in listening["sections"]:
            lines.append(f"**{section['name']}**（最多播放 {section['max_plays']} 次）")
            lines.append("")
            if section.get("shared_audio"):
                lines.append(f"短文原文：{section['passage_transcript'][0][1]}")
                lines.append("")
            lines.append("| 题号 | 原文/题干 | 答案 | 轨道 |")
            lines.append("|---:|---|---|---|")
            for question in section["questions"]:
                lines.append(f"| {question['id']} | {transcript_text(question)} | {answer_text(question)} | {question['tag']} |")
            lines.append("")
        lines.extend(["### 口语目标句", "", "| 题号 | 类型 | 示范问题/目标句 | 评测目标 | 轨道 |", "|---:|---|---|---|---|"])
        for question in speaking["questions"]:
            if question["type"] == "repeat":
                prompt = question["text"]
                target = question["text"]
            else:
                prompt = question["question"]
                target = question["expected"]
            lines.append(f"| {question['id']} | {question['type']} | {prompt} | {target} | {question['tag']} |")
        lines.append("")
    return "\n".join(lines)


def main():
    listening_courses = [build_listening(day) for day in range(1, 7)]
    speaking_courses = [build_speaking(day) for day in range(1, 7)]
    for course in listening_courses:
        json_write(LISTENING_OUT / f"{course['course_id']}.json", course)
    for course in speaking_courses:
        json_write(SPEAKING_OUT / f"{course['course_id']}.json", course)
    listening_catalog = []
    speaking_catalog = []
    for course in listening_courses:
        child = child_listening(course)
        json_write(CHILD_LISTENING_OUT / f"{course['course_id']}.json", child)
        listening_catalog.append({
            "course_id": course["course_id"], "course_version": child["course_version"],
            "title": course["title"], "course_type": course["course_type"],
            "week": course["week"], "day": course["day"], "visible": False,
            "pair_id": course["pair_id"], "study_pack": course["study_pack"],
        })
    for course in speaking_courses:
        child = child_speaking(course)
        json_write(CHILD_SPEAKING_OUT / f"{course['course_id']}.json", child)
        speaking_catalog.append({
            "course_id": course["course_id"], "course_version": child["course_version"],
            "title": course["title"], "course_type": course["course_type"],
            "week": course["week"], "day": course["day"], "visible": False,
            "pair_id": course["pair_id"], "study_pack": course["study_pack"],
        })
    json_write(CHILD_LISTENING_OUT / "catalog.json", listening_catalog)
    json_write(CHILD_SPEAKING_OUT / "catalog.json", speaking_catalog)
    json_write(OUT / "study-packs.json", build_study_packs(listening_courses, speaking_courses))
    json_write(OUT / "audio-generation-plan.json", build_audio_plan(listening_courses, speaking_courses))
    DOCS_OUT.mkdir(parents=True, exist_ok=True)
    (DOCS_OUT / "2026-09-01-4A-T1-W01教材与课程映射.md").write_text(
        build_mapping_doc(listening_courses, speaking_courses),
        encoding="utf-8",
        newline="\n",
    )
    (DOCS_OUT / "2026-09-01-4A-T1-W01家长版答案原文.md").write_text(
        build_parent_doc(listening_courses, speaking_courses),
        encoding="utf-8",
        newline="\n",
    )
    print("Built 6 listening + 6 speaking drafts, safe child copies, 6 study packs, and 168 audio text items.")


if __name__ == "__main__":
    main()
