# -*- coding: utf-8 -*-
"""Build the approved 4A Starter p2-p6 D01-D05 course package.

The active parent JSON files are the single authoritative course source. The
draft directory contains only pairing/audio plans and derived child-validation
copies. The five renumbered courses are published to the formal catalog.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BATCH = "4A-T1-W01"
LISTENING_OUT = ROOT / "content" / "listening"
SPEAKING_OUT = ROOT / "content" / "speaking"
DRAFT_OUT = ROOT / "content" / "drafts" / "4A-T1-W01-STARTER"
CHILD_LISTENING_OUT = DRAFT_OUT / "child" / "listening"
CHILD_SPEAKING_OUT = DRAFT_OUT / "child" / "speaking"
DOCS_OUT = ROOT / "docs" / "course-batches"
LISTENING_AUDIO_ROOT = ROOT / "static" / "audio" / "listening"
SPEAKING_AUDIO_ROOT = ROOT / "static" / "audio" / "speaking"


DAY_META = {
    1: {
        "lesson": 1,
        "title": "四上·Starter第1课｜认识家人、朋友和老师",
        "scope": "4A Starter p2-p3",
        "planned_difficulty": "L1",
        "json_difficulty": "L1",
        "listening_minutes": 12,
        "speaking_minutes": 8,
        "focus": "人物名称、家庭分组和老师称谓",
        "max_plays": [2, 2, 2, 2, 3],
    },
    2: {
        "lesson": 2,
        "title": "四上·Starter第2课｜在学校·听懂并回应",
        "scope": "4A Starter p2-p4",
        "planned_difficulty": "L1+",
        "json_difficulty": "L1",
        "listening_minutes": 12,
        "speaking_minutes": 8,
        "focus": "课堂请求、指令与自然回应",
        "max_plays": [2, 2, 2, 2, 3],
    },
    3: {
        "lesson": 3,
        "title": "四上·Starter第3课｜学习方法·勇敢尝试",
        "scope": "4A Starter p2-p5",
        "planned_difficulty": "L2",
        "json_difficulty": "L2",
        "listening_minutes": 17,
        "speaking_minutes": 8,
        "focus": "拼写、鼓励尝试、学习计划与表扬",
        "max_plays": [2, 2, 2, 2, 3],
    },
    4: {
        "lesson": 4,
        "title": "四上·Starter第4课｜数字20–100·准确听辨",
        "scope": "4A Starter p2-p6 Numbers",
        "planned_difficulty": "L2+",
        "json_difficulty": "L2",
        "listening_minutes": 17,
        "speaking_minutes": 8,
        "focus": "20–29、整十数和100的相似音辨别",
        "max_plays": [1, 2, 2, 2, 3],
    },
    5: {
        "lesson": 5,
        "title": "四上·Starter第5课｜星期表达·Starter综合",
        "scope": "4A Starter p2-p6 Days of the week and review",
        "planned_difficulty": "L3",
        "json_difficulty": "L3",
        "listening_minutes": 22,
        "speaking_minutes": 8,
        "focus": "星期顺序、前后关系与Starter综合",
        "max_plays": [1, 1, 2, 2, 3],
    },
}


def a(pages: str, focus: str) -> str:
    return f"A主线·{pages}·{focus}"


def c(pages: str, focus: str) -> str:
    return f"C微调·{pages}·{focus}"


def parent_note(tag: str) -> str:
    pages = tag.split("·", 2)[1]
    if tag.startswith("C微调"):
        return f"00确认的历史题型微调；语言材料仍只取确认版教材{pages}，不作未掌握结论"
    return f"确认版教材{pages}主线或不增加新知识的同语境受控重组"


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
        "words": [
            word("Shenshen", ["Shenshen", "Xinxin", "Xiaotian"], 0, a("p2", "教材人物直接识别")),
            word("Xiaopu", ["Xiaojiang", "Xiaopu", "Minmin"], 1, a("p2-p3", "教材人物直接识别")),
            word("Miss Li", ["Ms Yu", "Miss Li", "Mr Zhong"], 1, a("p3", "老师称谓与姓名")),
            word("Mr Qian", ["Mr Qian", "Miss Li", "Ms Yu"], 0, c("p3", "听音选词与称谓辨别")),
        ],
        "sentences": [
            sentence("This is Shenshen and her family.", "This is Shenshen and her family.", "same", a("p2", "家庭分组")),
            sentence("This is Xiaopu and Xiaojiang.", "This is Xiaopu and Xiaojiang.", "same", a("p2", "人物组合")),
            sentence("Lele is with Minmin and his family.", "Lele is with Minmin and his family.", "same", a("p3", "家庭人物对应")),
            sentence("Mr Zhong is a teacher.", "Mr Qian is a teacher.", "different", a("p3", "老师姓名辨别")),
        ],
        "responses": [
            response("Who is Shenshen's mum?", ["This is Shenshen's mum.", "This is Shenshen's dad.", "This is Shenshen's grandma."], 0, a("p2", "家庭称谓问答")),
            response("Who is Miss Li?", ["She is a teacher.", "She is Shenshen's mum.", "She is Minmin."], 0, c("p2-p3", "听问句选答语与人物称谓")),
            response("Who is with Minmin and his family?", ["Lele.", "Max.", "Mira."], 0, a("p2-p3", "人物信息对应")),
            response("Who are in the same family group?", ["Xiaopu and Xiaojiang.", "Yaoyao and James.", "Ms Yu and Mr Qian."], 0, a("p2-p3", "家庭分组对应")),
        ],
        "dialogues": [
            dialogue([["f", "This is Shenshen and her family."], ["m", "Hello, Shenshen."]], "Who is with her family?", ["Shenshen.", "Minmin.", "James."], 0, a("p2", "家庭人物识别")),
            dialogue([["f", "This is Xiaopu and Xiaojiang."], ["m", "They are with their family."]], "Who are together?", ["Xiaopu and Xiaojiang.", "Yaoyao and James.", "Ms Yu and Miss Li."], 0, a("p2-p3", "人物组合对应")),
            dialogue([["f", "This is Minmin and his family."], ["m", "Lele is with Minmin."]], "Who is with Minmin?", ["Lele.", "Mira.", "Max."], 0, a("p3", "家庭人物对应")),
            dialogue([["f", "This is Miss Li."], ["m", "She is a teacher."]], "Who is the teacher?", ["Miss Li.", "Xinxin.", "Lele."], 0, a("p3", "老师人物对应")),
        ],
        "passage": "This is Shenshen and her family. Grandma, Grandpa, Dad, Mum, Mira and Xinxin are with Shenshen. This is Xiaopu, Xiaojiang and their family. This is Minmin and his family. Lele is with Minmin. Ms Yu, Miss Li, Mr Zhong and Mr Qian are teachers.",
        "statements": [
            passage_statement("Xinxin is with Shenshen and her family.", True, a("p2", "家庭人物提取")),
            passage_statement("Xiaopu is with Minmin and his family.", False, a("p2-p3", "跨组人物判断")),
            passage_statement("Lele is with Minmin.", True, a("p3", "家庭人物提取")),
            passage_statement("Mr Qian is a teacher.", True, a("p3", "老师信息提取")),
        ],
    },
    2: {
        "words": [
            word("quiet", ["quiet", "pencil", "partner"], 0, a("p4", "课堂用语听辨")),
            word("red pencil", ["red pencil", "open books", "read the story"], 0, a("p4", "课堂物品短语")),
            word("open your books", ["read the story", "open your books", "please be quiet"], 1, a("p4", "课堂指令听辨")),
            word("partner", ["pencil", "partner", "story"], 1, c("p4", "听音选词")),
        ],
        "sentences": [
            sentence("Please be quiet.", "Please be quiet.", "same", a("p4", "课堂指令")),
            sentence("May I use your red pencil?", "May I use your red pencil?", "same", a("p4", "课堂请求")),
            sentence("Open your books, please.", "Read the story, please.", "different", a("p4", "相近课堂指令")),
            sentence("Read the story with your partner.", "Read the story with your partner.", "same", a("p4", "课堂指令")),
        ],
        "responses": [
            response("May I use your red pencil?", ["Here you are.", "Please be quiet.", "I win!"], 0, a("p4", "请求与回应")),
            response("Open your books, please.", ["All right, Miss Li.", "Here you are.", "I win!"], 0, c("p4", "听问句选答语")),
            response("Please be quiet.", ["All right, Miss Li.", "May I use your red pencil?", "Read the story with your partner."], 0, a("p4", "指令与回应")),
            response("Read the story with your partner.", ["All right, Miss Li.", "Here you are.", "Please be quiet."], 0, a("p4", "指令与回应")),
        ],
        "dialogues": [
            dialogue([["m", "I win!"], ["f", "Please be quiet."]], "What does the girl say?", ["Please be quiet.", "Here you are.", "Open your books, please."], 0, a("p4", "课堂情境对应")),
            dialogue([["f", "May I use your red pencil?"], ["m", "Here you are."]], "What does the boy say?", ["Here you are.", "I win!", "Please be quiet."], 0, a("p4", "借用物品情境")),
            dialogue([["f", "Open your books, please."], ["m", "All right, Miss Li."]], "What should they open?", ["Their books.", "The red pencil.", "The story."], 0, a("p4", "课堂指令取信息")),
            dialogue([["f", "Read the story with your partner."], ["m", "All right, Miss Li."]], "Who should read with you?", ["Your partner.", "Mr Zhong.", "Shenshen's mum."], 0, a("p2-p4", "课堂指令与人物角色")),
        ],
        "passage": "At school, Shenshen says, I win! Miss Li says, Please be quiet. Minmin asks, May I use your red pencil? James says, Here you are. Miss Li says, Open your books, please. Read the story with your partner. They say, All right, Miss Li.",
        "statements": [
            passage_statement("Shenshen says, I win!", True, a("p2-p4", "人物与课堂表达")),
            passage_statement("Miss Li asks for a red pencil.", False, a("p3-p4", "人物与请求对应")),
            passage_statement("James says, Here you are.", True, a("p3-p4", "人物与回应对应")),
            passage_statement("Miss Li asks them to read with a partner.", True, a("p3-p4", "跨句课堂指令")),
        ],
    },
    3: {
        "words": [
            word("spell", ["spell", "plan", "quiet"], 0, a("p5", "学习表达听辨")),
            word("book", ["book", "Weather", "plan"], 0, a("p5", "拼写对象")),
            word("English study", ["English study", "red pencil", "your partner"], 0, a("p4-p5", "学习短语")),
            word("Have a try", ["Well done", "Have a try", "Keep quiet"], 1, c("p5", "听音选表达")),
        ],
        "sentences": [
            sentence("How do you spell book?", "How do you spell book?", "same", a("p5", "拼写问句")),
            sentence("Don't be afraid!", "Don't be afraid!", "same", a("p5", "鼓励表达")),
            sentence("This is my plan for English study.", "This is my plan for English study.", "same", a("p5", "学习计划")),
            sentence("It's a good plan!", "Keep quiet, please.", "different", a("p5", "表达目的辨别")),
        ],
        "responses": [
            response("How do you spell book?", ["B-o-o-k.", "Weather.", "Have a try!"], 0, a("p5", "拼写问答")),
            response("Your partner is afraid. What do you say?", ["Don't be afraid! Have a try!", "Keep quiet, please.", "Here you are."], 0, a("p4-p5", "情境鼓励")),
            response("What do you say about a good English study plan?", ["Well done! It's a good plan!", "May I use your red pencil?", "Please be quiet."], 0, c("p4-p5", "听问句选恰当回应")),
            response("What do you say when someone should be quiet?", ["Keep quiet, please.", "B-o-o-k.", "I win!"], 0, a("p4-p5", "情境指令")),
        ],
        "dialogues": [
            dialogue([["f", "How do you spell book?"], ["m", "B-o-o-k."], ["f", "Well done!"]], "What does the boy spell?", ["Book.", "Weather.", "Plan."], 0, a("p5", "三轮拼写对话")),
            dialogue([["m", "I am afraid."], ["f", "Don't be afraid!"], ["f", "Have a try!"]], "What does the girl say?", ["She says, Have a try!", "She says, May I use your pencil?", "She says, Open your books, please."], 0, a("p4-p5", "三轮鼓励情境")),
            dialogue([["f", "This is my plan for English study."], ["m", "Well done!"], ["m", "It's a good plan!"]], "What does the boy think of the plan?", ["It is good.", "It is a red pencil.", "It is quiet."], 0, a("p5", "三轮信息整合")),
            dialogue([["m", "I win!"], ["f", "Please be quiet."], ["m", "All right, Miss Li."]], "What should the boy do?", ["Be quiet.", "Spell book.", "Use a red pencil."], 0, a("p4-p5", "前课螺旋复现")),
        ],
        "passage": "This is Shenshen's plan for English study. She asks, How do you spell book? James says, B-o-o-k. Minmin is afraid. Shenshen says, Don't be afraid! Have a try! Miss Li says, Well done! It's a good plan! Mr Zhong says, Keep quiet, please.",
        "statements": [
            passage_statement("Shenshen has a plan for English study.", True, a("p2-p5", "学习计划取信息")),
            passage_statement("James spells Weather.", False, a("p3-p5", "拼写内容对应")),
            passage_statement("Shenshen says, Have a try, to Minmin.", True, a("p2-p5", "跨句人物行为")),
            passage_statement("Mr Zhong says, Keep quiet, please.", True, a("p3-p5", "人物与表达对应")),
        ],
    },
    4: {
        "words": [
            word("twenty-four", ["twenty-four", "forty", "twenty-five"], 0, a("p6", "相似数字听辨")),
            word("sixty", ["sixteen", "sixty", "seventy"], 1, a("p6", "整十数听辨")),
            word("twenty-six", ["twenty-six", "sixty", "twenty-seven"], 0, a("p6", "相似数字听辨")),
            word("forty", ["twenty-four", "forty", "fifty"], 1, c("p6", "听音选词与相似数字")),
        ],
        "sentences": [
            sentence("twenty-eight", "twenty-eight", "same", a("p6", "数字直接判断")),
            sentence("seventy", "twenty-seven", "different", a("p6", "相似数字判断")),
            sentence("one hundred", "one hundred", "same", a("p6", "百位数判断")),
            sentence("twenty-five", "fifty", "different", a("p6", "相似数字判断")),
        ],
        "responses": [
            response("There are twenty-four girls. How many girls are there?", ["There are twenty-four girls.", "There are forty girls.", "There are twenty-five girls."], 0, a("p6", "虚构班级人数")),
            response("There are twenty-six boys. How many boys are there?", ["There are sixty boys.", "There are twenty-six boys.", "There are twenty-seven boys."], 1, a("p6", "虚构班级人数")),
            response("The number is eighty. What is the number?", ["It is twenty-eight.", "It is eighty.", "It is ninety."], 1, c("p6", "听问句选数字答语")),
            response("The number is one hundred. What is the number?", ["It is one hundred.", "It is ninety.", "It is thirty."], 0, a("p6", "百位数问答")),
        ],
        "dialogues": [
            dialogue([["f", "How many girls are there?"], ["m", "There are twenty-four girls."], ["f", "Twenty-four. All right."]], "How many girls are there?", ["Twenty-four.", "Forty.", "Twenty-five."], 0, a("p4-p6", "三轮人数对话")),
            dialogue([["m", "How many boys are there?"], ["f", "There are twenty-six boys."], ["m", "Twenty-six. Well done!"]], "How many boys are there?", ["Sixty.", "Twenty-six.", "Twenty-seven."], 1, a("p5-p6", "三轮人数对话")),
            dialogue([["f", "Please say the number."], ["m", "Forty."], ["f", "Please say the number after forty."], ["m", "Fifty."]], "What number does the boy say after forty?", ["Forty.", "Fifty.", "Sixty."], 1, a("p4-p6", "跨句数字提取")),
            dialogue([["m", "Eighty."], ["f", "Ninety."], ["m", "One hundred."]], "What number does the boy say after ninety?", ["Eighty.", "Ninety.", "One hundred."], 2, a("p6", "多数字信息提取")),
        ],
        "passage": "There are twenty-four girls and twenty-six boys in a class. Miss Li says forty. Mr Zhong says sixty. Ms Yu says eighty. Mr Qian says one hundred.",
        "statements": [
            passage_statement("There are twenty-four girls.", True, a("p3-p6", "人物数量提取")),
            passage_statement("There are sixty boys.", False, a("p6", "相似数字判断")),
            passage_statement("Mr Zhong says sixty.", True, a("p3-p6", "人物数字对应")),
            passage_statement("Mr Qian says ninety.", False, a("p3-p6", "跨句数字对应")),
        ],
    },
    5: {
        "words": [
            word("Monday", ["Monday", "Tuesday", "Sunday"], 0, a("p6", "星期直接识别")),
            word("Wednesday", ["Tuesday", "Wednesday", "Thursday"], 1, a("p6", "相邻星期辨别")),
            word("Friday", ["Thursday", "Friday", "Saturday"], 1, a("p6", "相邻星期辨别")),
            word("Sunday", ["Saturday", "Sunday", "Monday"], 1, a("p6", "相邻星期辨别")),
            word("Thursday", ["Tuesday", "Thursday", "Friday"], 1, c("p6", "听音选词与星期辨别")),
        ],
        "sentences": [
            sentence("Tuesday is after Monday.", "Tuesday is after Monday.", "same", a("p6", "星期顺序")),
            sentence("Friday is after Thursday.", "Saturday is after Thursday.", "different", a("p6", "跨一日干扰")),
            sentence("Sunday is after Saturday.", "Sunday is after Saturday.", "same", a("p6", "星期顺序")),
            sentence("My favourite day is Wednesday.", "My favourite day is Friday.", "different", a("p6", "最喜欢的星期")),
            sentence("On Tuesday, we read the story with a partner.", "On Tuesday, we read the story with a partner.", "same", a("p4-p6", "星期与课堂表达整合")),
        ],
        "responses": [
            response("What day is after Monday?", ["Tuesday.", "Sunday.", "Friday."], 0, a("p6", "星期顺序问答")),
            response("What day is after Tuesday?", ["Monday.", "Wednesday.", "Thursday."], 1, c("p6", "听问句选答语")),
            response("What day is after Friday?", ["Thursday.", "Saturday.", "Sunday."], 1, a("p6", "星期顺序问答")),
            response("What day is after Saturday?", ["Sunday.", "Monday.", "Friday."], 0, a("p6", "星期顺序问答")),
            response("Shenshen says, My favourite day is Sunday. What is Shenshen's favourite day?", ["Sunday.", "Saturday.", "Monday."], 0, a("p2-p6", "人物与星期信息")),
        ],
        "dialogues": [
            dialogue([["f", "What day is after Tuesday?"], ["m", "Wednesday."], ["f", "All right."]], "What day is after Tuesday?", ["Wednesday.", "Thursday.", "Monday."], 0, a("p4-p6", "三轮星期问答")),
            dialogue([["m", "On Monday, open your books, please."], ["f", "All right, Mr Zhong."], ["m", "On Tuesday, read the story with your partner."]], "What should they do on Tuesday?", ["Read the story with a partner.", "Open their books.", "Use a red pencil."], 0, a("p3-p6", "星期与课堂指令")),
            dialogue([["f", "On Wednesday, how do you spell book?"], ["m", "B-o-o-k."], ["f", "Well done!"], ["m", "All right."]], "What does the boy spell on Wednesday?", ["Book.", "Weather.", "Monday."], 0, a("p4-p6", "四轮星期学习情境")),
            dialogue([["m", "My favourite day is Friday."], ["f", "My favourite day is Sunday."], ["m", "Sunday is after Saturday."]], "What is the girl's favourite day?", ["Friday.", "Sunday.", "Saturday."], 1, a("p6", "人物与星期对应")),
            dialogue([["f", "On Thursday, this is my plan for English study."], ["m", "Have a try!"], ["f", "On Friday, I read the story."], ["m", "Well done!"]], "What does the girl do on Friday?", ["She reads the story.", "She uses a pencil.", "She spells Monday."], 0, a("p4-p6", "四轮Starter整合")),
        ],
        "passage": "This is our plan for English study. On Monday, we open our books. On Tuesday, we read the story with a partner. On Wednesday, we spell book. On Thursday, we say, Don't be afraid! Have a try! On Friday, Miss Li says, Well done! Saturday is after Friday. Sunday is after Saturday.",
        "statements": [
            passage_statement("They open their books on Monday.", True, a("p4-p6", "星期与课堂活动")),
            passage_statement("They spell book on Tuesday.", False, a("p5-p6", "跨句星期活动对应")),
            passage_statement("They say, Have a try, on Thursday.", True, a("p5-p6", "星期与鼓励表达")),
            passage_statement("Miss Li says, Well done, on Friday.", True, a("p3-p6", "人物星期对应")),
            passage_statement("Sunday is after Friday.", False, a("p6", "星期顺序综合")),
        ],
    },
}


SPEAKING_DATA = {
    1: [
        ("repeat", "This is Shenshen.", "", "", a("p2", "人物介绍")),
        ("repeat", "This is Shenshen and her family.", "", "", a("p2", "家庭介绍")),
        ("repeat", "This is Xiaopu and Xiaojiang.", "", "", a("p2", "人物组合")),
        ("repeat", "Lele is with Minmin and his family.", "", "", a("p3", "家庭人物对应")),
        ("repeat", "Ms Yu is a teacher.", "", "", a("p3", "老师介绍")),
        ("repeat", "Mr Zhong is a teacher.", "", "", a("p3", "老师介绍")),
        ("qa", "Is Miss Li a teacher?", "Yes. Miss Li is a teacher.", "回答：是的，Miss Li是一位老师。", c("p3", "听问句后准确回应")),
        ("qa", "Who is Shenshen's mum?", "This is Shenshen's mum.", "回答：这是Shenshen的妈妈。", a("p2", "家庭称谓问答")),
    ],
    2: [
        ("repeat", "I win!", "", "", a("p4", "课堂表达")),
        ("repeat", "Please be quiet.", "", "", a("p4", "课堂指令")),
        ("repeat", "May I use your red pencil?", "", "", a("p4", "课堂请求")),
        ("repeat", "Here you are.", "", "", a("p4", "自然回应")),
        ("repeat", "Open your books, please.", "", "", a("p4", "课堂指令")),
        ("repeat", "Read the story with your partner.", "", "", a("p4", "课堂指令")),
        ("qa", "May I use your red pencil?", "Here you are.", "递给对方并回答：给你。", c("p4", "听请求后准确回应")),
        ("qa", "Open your books, please.", "All right, Miss Li.", "回答Miss Li：好的。", a("p4", "听指令后回应")),
    ],
    3: [
        ("repeat", "How do you spell book?", "", "", a("p5", "拼写问句")),
        ("repeat", "B-o-o-k.", "", "", a("p5", "字母拼读")),
        ("repeat", "Don't be afraid!", "", "", a("p5", "鼓励表达")),
        ("repeat", "Have a try!", "", "", a("p5", "鼓励表达")),
        ("repeat", "This is my plan for English study.", "", "", a("p5", "学习计划")),
        ("repeat", "Well done! It's a good plan!", "", "", a("p5", "表扬表达")),
        ("qa", "How do you spell book?", "B-o-o-k.", "拼读单词book。", c("p5", "听问句后准确拼写")),
        ("qa", "Your friend is afraid. What do you say?", "Don't be afraid! Have a try!", "鼓励朋友：别害怕，试一试。", a("p5", "情境自主回应")),
    ],
    4: [
        ("repeat", "Twenty, twenty-one, twenty-two.", "", "", a("p6", "连续数字")),
        ("repeat", "Twenty-three, twenty-four, twenty-five.", "", "", a("p6", "连续数字")),
        ("repeat", "Twenty-six, twenty-seven, twenty-eight, twenty-nine.", "", "", a("p6", "连续数字")),
        ("repeat", "Thirty, forty, fifty.", "", "", a("p6", "整十数")),
        ("repeat", "Sixty, seventy, eighty, ninety.", "", "", a("p6", "整十数")),
        ("repeat", "One hundred.", "", "", a("p6", "百位数")),
        ("qa", "There are twenty-four girls. How many girls are there?", "There are twenty-four girls.", "完整回答：有24个女孩。", c("p6", "听问句后准确说数量")),
        ("qa", "There are twenty-six boys. How many boys are there?", "There are twenty-six boys.", "完整回答：有26个男孩。", a("p6", "数量完整回答")),
    ],
    5: [
        ("repeat", "Monday, Tuesday, Wednesday.", "", "", a("p6", "星期顺序")),
        ("repeat", "Thursday, Friday, Saturday, Sunday.", "", "", a("p6", "星期顺序")),
        ("repeat", "Tuesday is after Monday.", "", "", a("p6", "星期前后关系")),
        ("repeat", "Sunday is after Saturday.", "", "", a("p6", "星期前后关系")),
        ("repeat", "My favourite day is Sunday.", "", "", a("p6", "给定目标星期")),
        ("repeat", "On Tuesday, read the story with your partner.", "", "", a("p4-p6", "星期与课堂指令")),
        ("qa", "What day is after Tuesday?", "Wednesday.", "回答Tuesday之后是星期几。", c("p6", "听问句后准确回应")),
        ("qa", "What day is after Saturday?", "Sunday.", "回答Saturday之后是星期几。", a("p6", "星期顺序问答")),
    ],
}


SECTION_SPECS = [
    ("word_discrimination", "听音选词", "听录音，选出你听到的单词或短语", "words"),
    ("sentence_meaning", "听句判断", "听句子，判断和屏幕信息是否一致", "sentences"),
    ("question_response", "听问句选答语", "听问句，选出最合适的回答", "responses"),
    ("dialogue", "听对话选答案", "听连续对话和问题，选出正确答案", "dialogues"),
]


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
    sections = []
    start_id = 1
    for index, (section_id, name, tip, key) in enumerate(SECTION_SPECS):
        questions = data[key]
        sections.append(make_section(section_id, name, tip, meta["max_plays"][index], questions, course_id, start_id))
        start_id += len(questions)
    passage = make_section(
        "passage",
        "听短文判断",
        "先听完整短文，再判断每句话是否正确",
        meta["max_plays"][4],
        data["statements"],
        course_id,
        start_id,
    )
    passage["shared_audio"] = True
    passage["passage_audio"] = f"static/audio/listening/{course_id}/p01.mp3"
    passage["passage_transcript"] = [["n", data["passage"]]]
    sections.append(passage)
    count = sum(len(section["questions"]) for section in sections)
    expected_per_section = 4 if count == 20 else 5
    assert all(len(section["questions"]) == expected_per_section for section in sections)
    return {
        "course_id": course_id,
        "weekly_batch_id": BATCH,
        "study_pack": pair_id,
        "pair_id": pair_id,
        "publication_status": "formal",
        "title": meta["title"] + "（听力）",
        "week": 1,
        "day": day,
        "course_type": "training",
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
        "publication_status": "formal",
        "title": meta["title"] + "（口语）",
        "week": 1,
        "day": day,
        "course_type": "training",
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
        "publication_status": "formal",
        "expected_listening_outputs": 94,
        "expected_speaking_outputs": 40,
        "expected_total_outputs": 134,
        "items": items,
    }


def build_study_packs(listening_courses, speaking_courses):
    packs = []
    for listening, speaking in zip(listening_courses, speaking_courses):
        day = listening["day"]
        meta = DAY_META[day]
        packs.append({
            "lesson": meta["lesson"],
            "study_pack": listening["study_pack"],
            "pair_id": listening["pair_id"],
            "planned_title": meta["title"],
            "textbook_scope": meta["scope"],
            "planned_difficulty": meta["planned_difficulty"],
            "json_difficulty": meta["json_difficulty"],
            "planned_total_minutes": meta["listening_minutes"] + meta["speaking_minutes"],
            "focus": meta["focus"],
            "listening_course_id": listening["course_id"],
            "speaking_course_id": speaking["course_id"],
            "publication_gate": "须按老师实际已教页段逐课确认；制作完成不等于正式开放",
        })
    return {
        "weekly_batch_id": BATCH,
        "publication_status": "formal",
        "visible": True,
        "authority_note": "content/listening与content/speaking中的父JSON是唯一活动课程源；本目录仅保存派生校验材料。",
        "study_packs": packs,
    }


def build_mapping_doc(listening_courses, speaking_courses):
    lines = [
        "# 4A 新教材 Starter D01–D05 教材与课程映射",
        "",
        "> 状态：方案 A 正式发布稿；五组课程进入现有 formal 课程目录，不自动生成完成记录。",
        "",
        "## 教材事实边界",
        "",
        "- 唯一事实源：`content/curriculum/4A_2026/4A确认版教材/全册最终文件/`。",
        "- 本批只覆盖 Starter p2–6；Unit 1 从 p7 开始，本批不进入。",
        "- 旧教材 D01–D06 已从现行课程源与目录撤出，仅由 Git 历史保留；成绩和录音不删除。",
        "",
        "## 五课映射",
        "",
        "| 课次 | pair / study pack | 听力 | 口语 | 教材范围 | 难度 | 题量 | 总时长 | 重点 |",
        "|---|---|---|---|---|---|---:|---:|---|",
    ]
    for listening, speaking in zip(listening_courses, speaking_courses):
        meta = DAY_META[listening["day"]]
        count = sum(len(section["questions"]) for section in listening["sections"])
        lines.append(
            f"| 第{meta['lesson']}课 | {listening['pair_id']} | {listening['course_id']} | {speaking['course_id']} | "
            f"{meta['scope']} | {meta['planned_difficulty']}（JSON {meta['json_difficulty']}） | {count}+8 | "
            f"约{meta['listening_minutes'] + meta['speaking_minutes']}分钟 | {meta['focus']} |"
        )
    lines.extend([
        "",
        "## 螺旋与微调",
        "",
        "- D01：约90% p2–3主线、10%历史题型微调。",
        "- D02–D05：约70%本课新增范围、20%已教前课复现、10%历史题型微调。",
        "- 听力每课2道C题，口语每课1道C题；合计15/145，约10.3%。",
        "- C只改善听音选词和听问句后回应，不引入旧教材语言材料。",
        "",
        "## 正式开放闸门",
        "",
        "D01、D02、D03、D04、D05分别对应p2–3、p4、p5、p6 Numbers、p6 Days of the week；正式目录发布不制造完成状态，推荐课仍由实际 formal 完成记录决定。",
        "",
    ])
    return "\n".join(lines)


def build_parent_doc(listening_courses, speaking_courses):
    lines = [
        "# 4A 新教材 Starter D01–D05 家长版答案、原文与口语目标句",
        "",
        "> 家长专用。不得作为儿童公开副本；答案、原文和目标句不会写入儿童课程 JSON。",
        "",
    ]
    for listening, speaking in zip(listening_courses, speaking_courses):
        meta = DAY_META[listening["day"]]
        count = sum(len(section["questions"]) for section in listening["sections"])
        lines.extend([
            f"## 第{meta['lesson']}课｜{listening['course_id']} / {speaking['course_id']}",
            "",
            f"- 教材：{meta['scope']}；计划难度：{meta['planned_difficulty']}；听力{count}题，口语8题。",
            "",
            "### 听力答案与原文",
            "",
        ])
        for section in listening["sections"]:
            lines.append(f"**{section['name']}**（最多播放{section['max_plays']}次）")
            lines.append("")
            if section.get("shared_audio"):
                lines.append(f"短文原文：{section['passage_transcript'][0][1]}")
                lines.append("")
            lines.append("| 题号 | 原文/题干 | 答案 | 轨道 |")
            lines.append("|---:|---|---|---|")
            for question in section["questions"]:
                lines.append(f"| {question['id']} | {transcript_text(question)} | {answer_text(question)} | {question['tag']} |")
            lines.append("")
        lines.extend([
            "### 口语目标句",
            "",
            "| 题号 | 类型 | 示范问题/目标句 | 评测目标 | 轨道 |",
            "|---:|---|---|---|---|",
        ])
        for question in speaking["questions"]:
            prompt = question["text"] if question["type"] == "repeat" else question["question"]
            target = question["text"] if question["type"] == "repeat" else question["expected"]
            lines.append(f"| {question['id']} | {question['type']} | {prompt} | {target} | {question['tag']} |")
        lines.append("")
    return "\n".join(lines)


def remove_if_exists(path: Path):
    if path.exists():
        path.unlink()


def clean_obsolete_course_outputs():
    """Remove only generated term outputs superseded by the D01-D05 release."""
    for day in range(6, 12):
        remove_if_exists(LISTENING_OUT / f"L4A-T1-W01-D{day:02d}.json")
        remove_if_exists(SPEAKING_OUT / f"S4A-T1-W01-D{day:02d}.json")
    for day in range(1, 12):
        remove_if_exists(CHILD_LISTENING_OUT / f"L4A-T1-W01-D{day:02d}.json")
        remove_if_exists(CHILD_SPEAKING_OUT / f"S4A-T1-W01-D{day:02d}.json")
    for suffix in ("教材与课程映射", "家长版答案原文", "校验报告"):
        remove_if_exists(DOCS_OUT / f"2026-09-07-4A-Starter-D07-D11{suffix}.md")


def reset_renumbered_audio():
    """Clear exact generated course directories and manifest rows before rebuilding."""
    for module, prefix, audio_root in (
        ("listening", "L", LISTENING_AUDIO_ROOT),
        ("speaking", "S", SPEAKING_AUDIO_ROOT),
    ):
        course_ids = [f"{prefix}4A-T1-W01-D{day:02d}" for day in range(1, 12)]
        for course_id in course_ids:
            target = audio_root / course_id
            if target.is_dir():
                shutil.rmtree(target)
        manifest_path = audio_root / "manifest.json"
        if manifest_path.is_file():
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            courses = manifest.setdefault("courses", {})
            for course_id in course_ids:
                courses.pop(course_id, None)
            json_write(manifest_path, manifest)
        print(f"Reset {module} D01-D11 generated audio rows; D01-D05 must now be regenerated.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--reset-renumbered-audio",
        action="store_true",
        help="remove exact D01-D11 generated audio directories and manifest rows before rebuilding D01-D05",
    )
    args = parser.parse_args()
    clean_obsolete_course_outputs()
    if args.reset_renumbered_audio:
        reset_renumbered_audio()

    listening_courses = [build_listening(day) for day in range(1, 6)]
    speaking_courses = [build_speaking(day) for day in range(1, 6)]

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
            "course_id": course["course_id"],
            "course_version": child["course_version"],
            "title": course["title"],
            "course_type": course["course_type"],
            "week": course["week"],
            "day": course["day"],
            "visible": True,
            "pair_id": course["pair_id"],
            "study_pack": course["study_pack"],
        })
    for course in speaking_courses:
        child = child_speaking(course)
        json_write(CHILD_SPEAKING_OUT / f"{course['course_id']}.json", child)
        speaking_catalog.append({
            "course_id": course["course_id"],
            "course_version": child["course_version"],
            "title": course["title"],
            "course_type": course["course_type"],
            "week": course["week"],
            "day": course["day"],
            "visible": True,
            "pair_id": course["pair_id"],
            "study_pack": course["study_pack"],
        })

    json_write(CHILD_LISTENING_OUT / "catalog.json", listening_catalog)
    json_write(CHILD_SPEAKING_OUT / "catalog.json", speaking_catalog)
    json_write(DRAFT_OUT / "study-packs.json", build_study_packs(listening_courses, speaking_courses))
    json_write(DRAFT_OUT / "audio-generation-plan.json", build_audio_plan(listening_courses, speaking_courses))
    DOCS_OUT.mkdir(parents=True, exist_ok=True)
    (DOCS_OUT / "2026-09-07-4A-Starter-D01-D05教材与课程映射.md").write_text(
        build_mapping_doc(listening_courses, speaking_courses), encoding="utf-8", newline="\n"
    )
    (DOCS_OUT / "2026-09-07-4A-Starter-D01-D05家长版答案原文.md").write_text(
        build_parent_doc(listening_courses, speaking_courses), encoding="utf-8", newline="\n"
    )
    print("Built 5 listening + 5 speaking formal courses, 5 study packs, and 134 audio text items.")


if __name__ == "__main__":
    main()
