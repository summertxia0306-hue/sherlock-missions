# -*- coding: utf-8 -*-
"""Build the approved 4A Unit 2 p15-p22 D11-D15 formal package."""
from __future__ import annotations

from pathlib import Path

from build_4a_starter_courses import (
    a,
    answer_text,
    c,
    child_listening,
    child_speaking,
    dialogue,
    json_write,
    parent_note,
    passage_statement,
    response,
    sentence,
    transcript_text,
    word,
)


ROOT = Path(__file__).resolve().parents[1]
BATCH = "4A-T1-W01"
LISTENING_OUT = ROOT / "content" / "listening"
SPEAKING_OUT = ROOT / "content" / "speaking"
DRAFT_OUT = ROOT / "content" / "drafts" / "4A-T1-W01-UNIT2"
CHILD_LISTENING_OUT = DRAFT_OUT / "child" / "listening"
CHILD_SPEAKING_OUT = DRAFT_OUT / "child" / "speaking"
DOCS_OUT = ROOT / "docs" / "course-batches"


DAY_META = {
    11: {
        "lesson": 11,
        "title": "四上·第11课｜Unit 2认识新同学·人物特点",
        "scope": "4A Unit 2 p15-p16",
        "planned_difficulty": "L1",
        "json_difficulty": "L1",
        "listening_minutes": 12,
        "speaking_minutes": 8,
        "focus": "人物特点词、同学特点直接识别、基础介绍",
        "max_plays": [2, 2, 2, 2, 3],
    },
    12: {
        "lesson": 12,
        "title": "四上·第12课｜Unit 2我的同学·兴趣与梦想",
        "scope": "4A Unit 2 p15-p17",
        "planned_difficulty": "L1+",
        "json_difficulty": "L1",
        "listening_minutes": 14,
        "speaking_minutes": 8,
        "focus": "人物梦想、擅长项目、often与always",
        "max_plays": [2, 2, 2, 2, 3],
    },
    13: {
        "lesson": 13,
        "title": "四上·第13课｜Unit 2猜猜他是谁·人物信息",
        "scope": "4A Unit 2 p15-p19",
        "planned_difficulty": "L2",
        "json_difficulty": "L2",
        "listening_minutes": 17,
        "speaking_minutes": 8,
        "focus": "连续猜人对话、人物与行为对应、跨句判断",
        "max_plays": [2, 2, 2, 2, 3],
    },
    14: {
        "lesson": 14,
        "title": "四上·第14课｜Unit 2你能做到·故事整合",
        "scope": "4A Unit 2 p15-p21",
        "planned_difficulty": "L2+",
        "json_difficulty": "L2",
        "listening_minutes": 21,
        "speaking_minutes": 8,
        "focus": "跳长绳故事、问题解决结果、跨句信息整合",
        "max_plays": [1, 2, 2, 2, 3],
    },
    15: {
        "lesson": 15,
        "title": "四上·第15课｜Unit 2我的同学·综合猜人",
        "scope": "4A Unit 2 p15-p22",
        "planned_difficulty": "L3",
        "json_difficulty": "L3",
        "listening_minutes": 25,
        "speaking_minutes": 8,
        "focus": "Unit 2综合、跨题型猜人、稳定完整输出",
        "max_plays": [1, 1, 2, 2, 3],
    },
}


LISTENING_DATA = {
    11: {
        "words": [
            word("helpful", ["helpful", "friendly", "lovely"], 0, a("p15-p16", "人物特点词直接识别")),
            word("interesting", ["different", "interesting", "great"], 1, a("p15-p16", "人物特点词直接识别")),
            word("lovely", ["lovely", "clever", "cool"], 0, a("p15-p16", "人物特点词直接识别")),
            word("different", ["great", "different", "interesting"], 1, c("p15-p16", "听音选词与相似特点词辨别")),
        ],
        "sentences": [
            sentence("My classmates are lovely.", "My classmates are lovely.", "same", a("p15-p16", "人物特点直接理解")),
            sentence("They are different but all great.", "They are different but all great.", "same", a("p15-p16", "人物特点组合")),
            sentence("This classmate is helpful.", "This classmate is interesting.", "different", a("p15-p16", "相近特点词辨别")),
            sentence("We play a guessing game about classmates.", "We play a guessing game about classmates.", "same", a("p15", "单元任务理解")),
        ],
        "responses": [
            response("What are your classmates like?", ["They are lovely.", "They are in the classroom.", "They play football."], 0, a("p15-p16", "人物特点问答")),
            response("Is your classmate helpful?", ["Yes, she is.", "She is my classmate.", "It is great."], 0, c("p15-p16", "听问句选答语与人物特点辨别")),
            response("Are your classmates different?", ["Yes, they are.", "Yes, he is.", "They are classmates."], 0, a("p15-p16", "复数人物回应")),
            response("What game do we play?", ["A football game.", "A guessing game.", "A basketball game."], 1, a("p15", "单元任务问答")),
        ],
        "dialogues": [
            dialogue([["f", "This is my classmate."], ["m", "She is lovely."]], "What is the classmate like?", ["She is lovely.", "She is different.", "She is cool."], 0, a("p15-p16", "两轮特点提取")),
            dialogue([["m", "My classmates are different."], ["f", "Yes, but they are all great."]], "What are the classmates like?", ["They are the same.", "They are different but great.", "They are only interesting."], 1, a("p15-p16", "两轮特点整合")),
            dialogue([["f", "Who is helpful?"], ["m", "This girl is helpful."]], "Which word tells us about the girl?", ["Helpful.", "Lovely.", "Different."], 0, a("p15-p16", "人物特点对应")),
            dialogue([["m", "Let us play a guessing game."], ["f", "Great! Let us talk about our classmates."]], "Who is the game about?", ["Teachers.", "Classmates.", "Families."], 1, a("p15", "单元任务提取")),
        ],
        "passage": "Here are my classmates. They are different but all great. One classmate is lovely. One is interesting. Another classmate is very helpful. We play a guessing game about our classmates.",
        "statements": [
            passage_statement("The classmates are all the same.", False, a("p15-p16", "短文特点判断")),
            passage_statement("One classmate is interesting.", True, a("p15-p16", "短文信息提取")),
            passage_statement("Another classmate is helpful.", True, a("p15-p16", "人物特点提取")),
            passage_statement("They play a guessing game about teachers.", False, a("p15", "单元任务判断")),
        ],
    },
    12: {
        "words": [
            word("writer", ["writer", "painter", "football"], 0, a("p17", "梦想词直接识别")),
            word("painter", ["basketball", "painter", "writer"], 1, a("p17", "梦想词直接识别")),
            word("basketball", ["football", "basketball", "blackboard"], 1, a("p17", "运动词直接识别")),
            word("often", ["always", "often", "different"], 1, c("p17", "听音选词与频率词辨别")),
        ],
        "sentences": [
            sentence("Shenshen wants to be a writer.", "Shenshen wants to be a writer.", "same", a("p17", "人物梦想对应")),
            sentence("Xiaojiang wants to be a painter.", "Xiaojiang wants to be a writer.", "different", a("p17", "相近人物梦想辨别")),
            sentence("Minmin is good at football.", "Minmin is good at football.", "same", a("p17", "人物擅长项目对应")),
            sentence("Yaoyao often helps James with his Chinese.", "Yaoyao often helps James with his Chinese.", "same", a("p17", "频率与帮助行为")),
        ],
        "responses": [
            response("What does Shenshen want to be?", ["A writer.", "A painter.", "A football player."], 0, a("p17", "人物梦想问答")),
            response("Who is good at basketball?", ["Minmin.", "Xiaopu.", "Yaoyao."], 1, c("p17", "听问句选答语与人物信息对应")),
            response("What do Shenshen and Xiaojiang often do?", ["They share works with each other.", "They play basketball.", "They learn Chinese."], 0, a("p17", "共同行为问答")),
            response("What does Yaoyao always say?", ["Thank you.", "Please.", "Keep going."], 1, a("p17", "频率行为问答")),
        ],
        "dialogues": [
            dialogue([["f", "Shenshen wants to be a writer."], ["m", "Xiaojiang wants to be a painter."]], "What do they want to be?", ["A writer and a painter.", "Two painters.", "Two writers."], 0, a("p17", "两人物梦想整合")),
            dialogue([["m", "Minmin is good at football."], ["f", "Xiaopu is good at basketball."]], "Who is good at football?", ["Xiaopu.", "Minmin.", "Yaoyao."], 1, a("p17", "人物运动对应")),
            dialogue([["f", "Yaoyao is very nice."], ["m", "She often helps James with his Chinese."]], "Why is Yaoyao nice?", ["She helps James.", "She is a writer.", "She plays football."], 0, a("p17", "跨句原因提取")),
            dialogue([["m", "Our classmates are different."], ["f", "We always cheer for Minmin and Xiaopu."]], "What do they do for Minmin and Xiaopu?", ["They share works.", "They cheer for them.", "They clean the blackboard."], 1, a("p17", "频率行为提取")),
        ],
        "passage": "Shenshen wants to be a writer and Xiaojiang wants to be a painter. They often share works with each other. Minmin is good at football and Xiaopu is good at basketball. We always cheer for them. Yaoyao often helps James with his Chinese.",
        "statements": [
            passage_statement("Shenshen wants to be a painter.", False, a("p17", "人物梦想判断")),
            passage_statement("Shenshen and Xiaojiang often share works.", True, a("p17", "共同行为判断")),
            passage_statement("Xiaopu is good at basketball.", True, a("p17", "人物运动判断")),
            passage_statement("Yaoyao helps James with his English.", False, a("p17", "语言信息辨别")),
        ],
    },
    13: {
        "words": [
            word("lovely smile", ["lovely smile", "helpful classmate", "interesting story"], 0, a("p18", "人物线索短语识别")),
            word("interesting stories", ["different stories", "interesting stories", "lovely stories"], 1, a("p18-p19", "人物行为短语识别")),
            word("clean the blackboard", ["clean the room", "learn English", "clean the blackboard"], 2, a("p18-p19", "帮助行为识别")),
            word("learn English", ["learn Chinese", "learn English", "tell stories"], 1, c("p18-p19", "听音选词与相近帮助行为辨别")),
        ],
        "sentences": [
            sentence("James has a lovely smile.", "James has a lovely smile.", "same", a("p18", "人物外貌线索")),
            sentence("He often tells interesting stories.", "He often tells interesting stories.", "same", a("p18-p19", "人物频率行为")),
            sentence("Xiaopu always helps teachers clean the room.", "Xiaopu always helps teachers clean the blackboard.", "different", a("p19", "相近帮助行为辨别")),
            sentence("Wenwen always helps his little brother clean the room.", "Wenwen always helps his little brother clean the room.", "same", a("p19", "人物帮助行为对应")),
        ],
        "responses": [
            response("Who often tells interesting stories?", ["James.", "Minmin.", "Wenwen."], 0, a("p18-p19", "人物行为问答")),
            response("Who always helps teachers clean the blackboard?", ["Wenwen.", "Xiaopu.", "James."], 1, c("p18-p19", "听问句选答语与人物信息对应")),
            response("How does James help other students?", ["He helps them learn English.", "He cleans the room.", "He plays football."], 0, a("p18-p19", "帮助行为问答")),
            response("Is James helpful too?", ["Yes, he is.", "No, he is not.", "He is James."], 0, a("p18", "猜人对话回应")),
        ],
        "dialogues": [
            dialogue([["f", "He has a lovely smile and many friends."], ["m", "Is he Minmin?"], ["f", "No, he is not."]], "Is the classmate Minmin?", ["Yes.", "No.", "We do not know."], 1, a("p18", "连续猜人对话")),
            dialogue([["m", "He is interesting and often tells interesting stories."], ["f", "Is he Xiaopu?"], ["m", "No."]], "Which word describes the classmate?", ["Interesting.", "Different.", "Afraid."], 0, a("p18", "连续线索提取")),
            dialogue([["f", "He always helps teachers clean the blackboard."], ["m", "He also helps other students learn English."]], "What two things does he do?", ["He cleans and helps students learn.", "He paints and plays football.", "He skips and tells stories."], 0, a("p18-p19", "跨句行为整合")),
            dialogue([["m", "Who is he?"], ["f", "It is you, James. You are helpful too."]], "Who is the helpful classmate?", ["James.", "Minmin.", "Wenwen."], 0, a("p18", "猜人结果提取")),
        ],
        "passage": "This classmate has a lovely smile and many friends. He is interesting and often tells interesting stories. He is helpful too. He always helps teachers clean the blackboard and often helps other students learn English. It is James.",
        "statements": [
            passage_statement("The classmate has a lovely smile.", True, a("p18", "人物外貌提取")),
            passage_statement("He has no friends.", False, a("p18", "人物信息判断")),
            passage_statement("He helps teachers clean the blackboard.", True, a("p18-p19", "帮助行为提取")),
            passage_statement("The classmate is Minmin.", False, a("p18", "跨句猜人判断")),
        ],
    },
    14: {
        "words": [
            word("long rope", ["long rope", "lovely smile", "little brother"], 0, a("p20", "故事物品识别")),
            word("take it easy", ["keep going", "take it easy", "come on"], 1, a("p20", "安慰语识别")),
            word("jump over it", ["jump over it", "clean it", "turn it"], 0, a("p20", "动作指令识别")),
            word("excited", ["afraid", "excited", "helpful"], 1, a("p20-p21", "情绪变化识别")),
            word("keep going", ["take it easy", "keep going", "wait and jump"], 1, c("p20-p21", "听音选词与相近鼓励语辨别")),
        ],
        "sentences": [
            sentence("The classmates are skipping with a long rope.", "The classmates are skipping with a long rope.", "same", a("p20", "故事场景理解")),
            sentence("James feels great at first.", "James feels bad at first.", "different", a("p20", "初始情绪辨别")),
            sentence("Minmin shows James how to jump.", "Minmin shows James how to jump.", "same", a("p20", "帮助行为判断")),
            sentence("Shenshen and Xiaojiang turn the rope faster.", "Shenshen and Xiaojiang turn the rope more slowly.", "different", a("p20", "解决办法辨别")),
            sentence("James is happy and excited at the end.", "James is happy and excited at the end.", "same", a("p21", "故事结果与情绪")),
        ],
        "responses": [
            response("What are the classmates doing?", ["They are skipping.", "They are painting.", "They are cleaning."], 0, a("p20", "故事场景问答")),
            response("How does James feel before he jumps in?", ["He is afraid.", "He is excited.", "He is interesting."], 0, a("p20", "人物情绪问答")),
            response("Who shows James how to jump?", ["Shenshen.", "Minmin.", "Xiaojiang."], 1, c("p20", "听问句选答语与人物信息对应")),
            response("What do the classmates say to James?", ["You can do it!", "Please clean it!", "Tell a story!"], 0, a("p20", "鼓励语问答")),
            response("What does James say at the end?", ["I did it! Thank you!", "Take it easy!", "Wait and jump!"], 0, a("p21", "故事结果问答")),
        ],
        "dialogues": [
            dialogue([["m", "I cannot jump in."], ["f", "Take it easy. Wait and jump over the rope."]], "What should James do?", ["Wait and jump.", "Clean the room.", "Tell a story."], 0, a("p20", "两轮建议提取")),
            dialogue([["f", "Come on, James! You can do it!"], ["m", "But I am afraid."], ["f", "We can turn the rope more slowly."]], "How do the classmates help James?", ["They slow the rope.", "They stop the game.", "They leave James."], 0, a("p20", "连续对话解决办法")),
            dialogue([["m", "One, two, three!"], ["f", "James jumps in and skips."], ["m", "Keep going!"]], "What does James do?", ["He jumps in and skips.", "He ducks again.", "He cleans the blackboard."], 0, a("p21", "动作序列提取")),
            dialogue([["f", "The classmates cheer for James."], ["m", "I did it! Thank you!"]], "How does James feel now?", ["Happy and excited.", "Bad and afraid.", "Different and helpful."], 0, a("p21", "结果情绪推断")),
            dialogue([["m", "What is the problem?"], ["f", "James cannot jump in."], ["m", "What is the solution?"], ["f", "His classmates help him."]], "What is the solution?", ["His classmates help him.", "James goes home.", "The rope turns faster."], 0, a("p20-p21", "问题与解决办法整合")),
        ],
        "passage": "James and his classmates are skipping with a long rope. James is afraid and cannot jump in. Minmin shows him how. Shenshen and Xiaojiang turn the rope more slowly. His classmates say, You can do it. James jumps in and skips. They cheer for him. James is happy and excited.",
        "statements": [
            passage_statement("James is afraid at first.", True, a("p20", "故事问题提取")),
            passage_statement("Minmin tells James to clean the blackboard.", False, a("p20", "人物行为判断")),
            passage_statement("The rope turns more slowly to help James.", True, a("p20", "解决办法提取")),
            passage_statement("James ducks and never jumps in.", False, a("p20-p21", "结果判断")),
            passage_statement("The result is that James skips and feels excited.", True, a("p21", "故事结果整合")),
        ],
    },
    15: {
        "words": [
            word("helpful classmate", ["helpful classmate", "interesting story", "lovely smile"], 0, a("p15-p22", "综合人物特点识别")),
            word("painting pictures", ["playing football", "painting pictures", "telling stories"], 1, a("p17-p22", "梦想与活动短语识别")),
            word("often helps", ["always says", "often helps", "often tells"], 1, a("p17-p19", "频率行为短语辨别")),
            word("guessing game", ["skipping game", "guessing game", "football game"], 1, a("p15-p22", "单元任务识别")),
            word("blackboard", ["basketball", "blackboard", "classmate"], 1, c("p18-p19", "听音选词与相近词辨别")),
        ],
        "sentences": [
            sentence("Here are my lovely classmates.", "Here are my lovely classmates.", "same", a("p17", "韵文信息复现")),
            sentence("Shenshen and Xiaojiang often share works.", "Shenshen and Xiaojiang often share works.", "same", a("p17", "人物行为对应")),
            sentence("James always helps other students learn Chinese.", "James often helps other students learn English.", "different", a("p18-p19", "频率与语言双重辨别")),
            sentence("The solution is to turn the rope more slowly.", "The solution is to turn the rope more slowly.", "same", a("p20-p21", "故事结构理解")),
            sentence("The project is a guessing game about classmates.", "The project is a guessing game about classmates.", "same", a("p22", "项目任务理解")),
        ],
        "responses": [
            response("Who wants to be a painter?", ["Xiaojiang.", "Shenshen.", "Minmin."], 0, a("p17", "人物梦想问答")),
            response("Who often helps James with his Chinese?", ["Yaoyao.", "Wenwen.", "Xiaopu."], 0, c("p17", "听问句选答语与人物信息对应")),
            response("What does James often tell?", ["Interesting stories.", "The time.", "A problem."], 0, a("p18-p19", "人物行为问答")),
            response("What is the result of the rope story?", ["James jumps in and skips.", "James cleans the room.", "James tells a story."], 0, a("p20-p21", "故事结果问答")),
            response("What do we make for the project?", ["A guessing game.", "A school building.", "A long rope."], 0, a("p22", "项目任务问答")),
        ],
        "dialogues": [
            dialogue([["f", "She is friendly and helpful."], ["m", "Does she help you draw?"], ["f", "Yes. She is good at painting pictures."]], "What is the classmate good at?", ["Painting pictures.", "Playing basketball.", "Telling stories."], 0, a("p22", "项目猜人线索整合")),
            dialogue([["m", "He has a lovely smile."], ["f", "He often tells interesting stories."], ["m", "Is he James?"], ["f", "Yes, he is."]], "Who is the classmate?", ["James.", "Xiaopu.", "Minmin."], 0, a("p18", "多线索猜人")),
            dialogue([["f", "Minmin is good at football."], ["m", "Xiaopu is good at basketball."], ["f", "We always cheer for them."]], "Who is good at basketball?", ["Minmin.", "Xiaopu.", "James."], 1, a("p17", "跨句人物对应")),
            dialogue([["m", "James is afraid of the long rope."], ["f", "His classmates slow it down and cheer for him."], ["m", "Then he jumps in and skips."]], "Why can James do it?", ["His classmates help and cheer for him.", "He leaves the game.", "He turns the rope alone."], 0, a("p20-p21", "故事因果整合")),
            dialogue([["f", "She always says please and often helps James with his Chinese."], ["m", "Is she Yaoyao?"], ["f", "Yes."]], "Which two clues tell us about Yaoyao?", ["She says please and helps James.", "She paints and plays football.", "She cleans and tells stories."], 0, a("p17", "双线索人物判断")),
        ],
        "passage": "We are making a guessing game about my classmates. One girl is friendly and helpful. She often helps me draw. She is good at painting pictures and wants to be a painter. Another classmate is interesting and often tells stories. In our class, different classmates help and cheer for each other.",
        "statements": [
            passage_statement("The girl is friendly and helpful.", True, a("p22", "项目人物特点提取")),
            passage_statement("She is good at playing football.", False, a("p22", "擅长项目辨别")),
            passage_statement("She wants to be a painter.", True, a("p22", "人物梦想提取")),
            passage_statement("Another classmate often tells stories.", True, a("p18-p19", "跨人物信息提取")),
            passage_statement("All classmates are the same.", False, a("p15-p22", "单元主题综合判断")),
        ],
    },
}


SPEAKING_DATA = {
    11: [
        ("repeat", "Here are my lovely classmates.", "", "", a("p15-p16", "人物特点基础句")),
        ("repeat", "They are different but all great.", "", "", a("p15-p16", "人物特点组合句")),
        ("repeat", "This classmate is helpful.", "", "", a("p15-p16", "人物特点基础句")),
        ("repeat", "My classmate is interesting.", "", "", a("p15-p16", "人物特点基础句")),
        ("repeat", "She is friendly and lovely.", "", "", a("p16", "同语境特点组合")),
        ("repeat", "Let us play a guessing game about classmates.", "", "", a("p15", "单元任务句")),
        ("qa", "What are your classmates like?", "They are different but all great.", "用完整句说同学们的特点。", c("p15-p16", "自主问答与特点信息组织")),
        ("qa", "Is your classmate helpful?", "Yes, my classmate is helpful.", "用完整句回答并重复人物特点。", a("p15-p16", "基础问答输出")),
    ],
    12: [
        ("repeat", "Shenshen wants to be a writer.", "", "", a("p17", "人物梦想句")),
        ("repeat", "Xiaojiang wants to be a painter.", "", "", a("p17", "人物梦想句")),
        ("repeat", "They often share works with each other.", "", "", a("p17", "频率行为句")),
        ("repeat", "Minmin is good at football.", "", "", a("p17", "擅长项目句")),
        ("repeat", "Xiaopu is good at basketball.", "", "", a("p17", "擅长项目句")),
        ("repeat", "Yaoyao often helps James with his Chinese.", "", "", a("p17", "帮助行为句")),
        ("qa", "Who is good at basketball?", "Xiaopu is good at basketball.", "用人物名和完整句回答。", c("p17", "自主问答与人物信息对应")),
        ("qa", "What does Shenshen want to be?", "Shenshen wants to be a writer.", "用完整句回答人物梦想。", a("p17", "人物梦想问答")),
    ],
    13: [
        ("repeat", "He has a lovely smile and many friends.", "", "", a("p18", "人物外貌线索句")),
        ("repeat", "He often tells interesting stories.", "", "", a("p18-p19", "人物频率行为句")),
        ("repeat", "He always helps teachers clean the blackboard.", "", "", a("p18-p19", "人物帮助行为句")),
        ("repeat", "James often helps other students learn English.", "", "", a("p18-p19", "人物帮助行为句")),
        ("repeat", "Wenwen always helps his little brother clean the room.", "", "", a("p19", "规则例句复现")),
        ("repeat", "It is you, James. You are helpful too.", "", "", a("p18", "猜人结果句")),
        ("qa", "Who always helps teachers clean the blackboard?", "Xiaopu always helps teachers clean the blackboard.", "先说人物，再完整复述帮助行为。", c("p19", "自主问答与人物行为对应")),
        ("qa", "Why is James helpful?", "He often helps other students learn English.", "用教材中的帮助行为完整回答。", a("p18-p19", "跨句人物说明")),
    ],
    14: [
        ("repeat", "The classmates are skipping with a long rope.", "", "", a("p20", "故事场景句")),
        ("repeat", "Take it easy. Wait and jump over it.", "", "", a("p20", "安慰与动作指令")),
        ("repeat", "Minmin shows James how to jump.", "", "", a("p20", "帮助行为句")),
        ("repeat", "Come on, James! You can do it!", "", "", a("p20", "鼓励语")),
        ("repeat", "Shenshen and Xiaojiang turn the rope more slowly.", "", "", a("p20", "解决办法句")),
        ("repeat", "James is happy and excited at the end.", "", "", a("p21", "结果情绪句")),
        ("qa", "Who shows James how to jump?", "Minmin shows James how to jump.", "用人物名和完整动作句回答。", c("p20", "自主问答与人物信息对应")),
        ("qa", "What is the result of the story?", "James jumps in and skips with his classmates.", "用完整句说出故事结果。", a("p20-p21", "故事结果整合输出")),
    ],
    15: [
        ("repeat", "My classmates are different but all great.", "", "", a("p15-p22", "单元主题综合句")),
        ("repeat", "She is friendly and helpful.", "", "", a("p22", "项目人物特点句")),
        ("repeat", "She often helps me draw.", "", "", a("p22", "项目帮助行为句")),
        ("repeat", "She is good at painting pictures.", "", "", a("p22", "项目擅长句")),
        ("repeat", "She wants to be a painter.", "", "", a("p17-p22", "项目梦想句")),
        ("repeat", "The problem has a solution, and the result is great.", "", "", a("p20-p21", "故事结构同语境整合")),
        ("qa", "Who often helps James with his Chinese?", "Yaoyao often helps James with his Chinese.", "用人物名、频率词和帮助行为完整回答。", c("p17", "自主问答与人物信息对应")),
        ("qa", "Can you describe a helpful classmate?", "My classmate is helpful and often helps me draw.", "用特点加一个帮助行为完成猜人描述。", a("p15-p22", "项目综合稳定输出")),
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
    return {"id": section_id, "name": name, "tip": tip, "max_plays": max_plays, "questions": built}


def build_listening(day):
    meta = DAY_META[day]
    data = LISTENING_DATA[day]
    course_id = f"L4A-T1-W01-D{day:02d}"
    pair_id = f"4A-T1-W01-D{day:02d}"
    sections = []
    start_id = 1
    for index, (section_id, name, tip, key) in enumerate(SECTION_SPECS):
        source = data[key]
        sections.append(make_section(section_id, name, tip, meta["max_plays"][index], source, course_id, start_id))
        start_id += len(source)
    passage = make_section("passage", "听短文判断", "先听完整短文，再判断每句话是否正确", meta["max_plays"][4], data["statements"], course_id, start_id)
    passage.update({"shared_audio": True, "passage_audio": f"static/audio/listening/{course_id}/p01.mp3", "passage_transcript": [["n", data["passage"]]]})
    sections.append(passage)
    count = sum(len(section["questions"]) for section in sections)
    per_section = 4 if count == 20 else 5
    assert all(len(section["questions"]) == per_section for section in sections)
    return {
        "course_id": course_id,
        "weekly_batch_id": BATCH,
        "study_pack": pair_id,
        "pair_id": pair_id,
        "publication_status": "formal",
        "title": meta["title"] + "（听力）",
        "week": 3,
        "day": day - 10,
        "course_type": "weekly_test" if day == 15 else "training",
        "est_minutes": meta["listening_minutes"],
        "scope": meta["scope"],
        "difficulty": meta["json_difficulty"],
        "scoring": {"per_question": 5 if count == 20 else 4, "total": 100},
        "test_audio": f"static/audio/listening/{course_id}/hello.mp3",
        "test_transcript": [["n", "Hello! Can you hear me? Let us begin."]],
        "sections": sections,
    }


def build_speaking(day):
    meta = DAY_META[day]
    course_id = f"S4A-T1-W01-D{day:02d}"
    pair_id = f"4A-T1-W01-D{day:02d}"
    questions = []
    for index, (kind, prompt, expected, hint, tag) in enumerate(SPEAKING_DATA[day], 1):
        question = {"id": index, "type": kind, "audio": f"static/audio/speaking/{course_id}/q{index:02d}.mp3", "tag": tag, "parent_note": parent_note(tag)}
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
        "week": 3,
        "day": day - 10,
        "course_type": "weekly_review" if day == 15 else "training",
        "est_minutes": meta["speaking_minutes"],
        "scope": meta["scope"],
        "difficulty": meta["json_difficulty"],
        "questions": questions,
    }


def build_audio_plan(listening_courses, speaking_courses):
    items = []
    for course in listening_courses:
        items.append({"module": "listening", "course_id": course["course_id"], "kind": "test_audio", "path": course["test_audio"], "clips": course["test_transcript"]})
        for section in course["sections"]:
            if section.get("shared_audio"):
                items.append({"module": "listening", "course_id": course["course_id"], "kind": "passage", "path": section["passage_audio"], "clips": section["passage_transcript"]})
            for question in section["questions"]:
                if question.get("audio"):
                    items.append({"module": "listening", "course_id": course["course_id"], "kind": f"question_{question['id']:02d}", "path": question["audio"], "clips": question["transcript"]})
    listening_count = len(items)
    for course in speaking_courses:
        for question in course["questions"]:
            spoken = question["text"] if question["type"] == "repeat" else question["question"]
            items.append({"module": "speaking", "course_id": course["course_id"], "kind": f"question_{question['id']:02d}_{question['type']}", "path": question["audio"], "clips": [["n", spoken]]})
    speaking_count = len(items) - listening_count
    return {
        "weekly_batch_id": BATCH,
        "generation_status": "READY_TO_GENERATE",
        "publication_status": "formal",
        "expected_listening_outputs": listening_count,
        "expected_speaking_outputs": speaking_count,
        "expected_total_outputs": len(items),
        "items": items,
    }


def build_study_packs(listening_courses, speaking_courses):
    return {
        "weekly_batch_id": BATCH,
        "publication_status": "formal",
        "visible": True,
        "authority_note": "父JSON是唯一活动课程源；本目录保存配对、音频计划和派生儿童安全校验副本。课程完成后默认formal开放。",
        "study_packs": [
            {
                "lesson": DAY_META[day]["lesson"],
                "study_pack": listening["study_pack"],
                "pair_id": listening["pair_id"],
                "planned_title": DAY_META[day]["title"],
                "textbook_scope": DAY_META[day]["scope"],
                "planned_difficulty": DAY_META[day]["planned_difficulty"],
                "json_difficulty": DAY_META[day]["json_difficulty"],
                "planned_total_minutes": DAY_META[day]["listening_minutes"] + DAY_META[day]["speaking_minutes"],
                "focus": DAY_META[day]["focus"],
                "listening_course_id": listening["course_id"],
                "speaking_course_id": speaking["course_id"],
                "publication_gate": "课程完成后默认formal开放；家长负责按实际学习进度依次使用。",
            }
            for day, listening, speaking in zip(range(11, 16), listening_courses, speaking_courses)
        ],
    }


def build_mapping_doc(listening_courses, speaking_courses):
    lines = [
        "# 4A 新教材 Unit 2 D11–D15 教材与课程映射",
        "",
        "> formal发布稿。教材事实源为确认版教材逐页转录，范围严格为Unit 2 p15–22。",
        "",
        "| 课次 | pair / study pack | 听力 | 口语 | 教材范围 | 难度 | 题量 | 总时长 | 重点 |",
        "|---|---|---|---|---|---|---:|---:|---|",
    ]
    for day, listening, speaking in zip(range(11, 16), listening_courses, speaking_courses):
        meta = DAY_META[day]
        count = sum(len(section["questions"]) for section in listening["sections"])
        lines.append(f"| 第{day}课 | {listening['pair_id']} | {listening['course_id']} | {speaking['course_id']} | {meta['scope']} | {meta['planned_difficulty']}（JSON {meta['json_difficulty']}） | {count}+8 | 约{meta['listening_minutes'] + meta['speaking_minutes']}分钟 | {meta['focus']} |")
    lines += [
        "",
        "## 开放规则",
        "",
        "- 按家长已确认的D34决策：课程完成后默认formal开放，不再按学校逐页设置发布闸门。",
        "- 夏洛恪与家长按实际进度从推荐课开始逐课完成；开放不等于完成，也不自动产生学习记录。",
        "- 全批不进入Unit 3 p23及以后内容，不制造test或formal学习记录。",
        "",
        "## A主线与C微调",
        "",
        "- 150题中A主线135题、C微调15题；C占10%。",
        "- 每门听力2道C题：1道听音选词、1道听问句选答语；每门口语1道C题：QA。",
        "- C只提高历史相对低正确率题型及人物信息对应的辨别质量，语言材料仍取Unit 2 p15–22，不作未掌握结论。",
        "",
    ]
    return "\n".join(lines)


def build_parent_doc(listening_courses, speaking_courses):
    lines = [
        "# 4A 新教材 Unit 2 D11–D15 家长版答案、原文与口语目标句",
        "",
        "> 家长专用。不得作为儿童公开副本；课程为formal发布稿。",
        "",
    ]
    for day, listening, speaking in zip(range(11, 16), listening_courses, speaking_courses):
        meta = DAY_META[day]
        count = sum(len(section["questions"]) for section in listening["sections"])
        lines += [f"## 第{day}课｜{listening['course_id']} / {speaking['course_id']}", "", f"- 教材：{meta['scope']}；计划难度：{meta['planned_difficulty']}；听力{count}题，口语8题。", "", "### 听力答案与原文", ""]
        for section in listening["sections"]:
            lines += [f"**{section['name']}**（最多播放{section['max_plays']}次）", ""]
            if section.get("shared_audio"):
                lines += [f"短文原文：{section['passage_transcript'][0][1]}", ""]
            lines += ["| 题号 | 原文/题干 | 答案 | 轨道 |", "|---:|---|---|---|"]
            for question in section["questions"]:
                lines.append(f"| {question['id']} | {transcript_text(question)} | {answer_text(question)} | {question['tag']} |")
            lines.append("")
        lines += ["### 口语目标句", "", "| 题号 | 类型 | 示范问题/目标句 | 评测目标 | 轨道 |", "|---:|---|---|---|---|"]
        for question in speaking["questions"]:
            prompt = question["text"] if question["type"] == "repeat" else question["question"]
            target = question["text"] if question["type"] == "repeat" else question["expected"]
            lines.append(f"| {question['id']} | {question['type']} | {prompt} | {target} | {question['tag']} |")
        lines.append("")
    return "\n".join(lines)


def child_catalog_entry(course, child):
    return {
        "course_id": course["course_id"],
        "course_version": child["course_version"],
        "title": course["title"],
        "course_type": course["course_type"],
        "week": course["week"],
        "day": course["day"],
        "visible": True,
        "pair_id": course["pair_id"],
        "study_pack": course["study_pack"],
    }


def main():
    listening_courses = [build_listening(day) for day in range(11, 16)]
    speaking_courses = [build_speaking(day) for day in range(11, 16)]
    listening_catalog = []
    speaking_catalog = []
    for course in listening_courses:
        json_write(LISTENING_OUT / f"{course['course_id']}.json", course)
        child = child_listening(course)
        json_write(CHILD_LISTENING_OUT / f"{course['course_id']}.json", child)
        listening_catalog.append(child_catalog_entry(course, child))
    for course in speaking_courses:
        json_write(SPEAKING_OUT / f"{course['course_id']}.json", course)
        child = child_speaking(course)
        json_write(CHILD_SPEAKING_OUT / f"{course['course_id']}.json", child)
        speaking_catalog.append(child_catalog_entry(course, child))
    json_write(CHILD_LISTENING_OUT / "catalog.json", listening_catalog)
    json_write(CHILD_SPEAKING_OUT / "catalog.json", speaking_catalog)
    json_write(DRAFT_OUT / "study-packs.json", build_study_packs(listening_courses, speaking_courses))
    json_write(DRAFT_OUT / "audio-generation-plan.json", build_audio_plan(listening_courses, speaking_courses))
    DOCS_OUT.mkdir(parents=True, exist_ok=True)
    (DOCS_OUT / "2026-09-11-4A-Unit2-D11-D15教材与课程映射.md").write_text(build_mapping_doc(listening_courses, speaking_courses), encoding="utf-8", newline="\n")
    (DOCS_OUT / "2026-09-11-4A-Unit2-D11-D15家长版答案原文.md").write_text(build_parent_doc(listening_courses, speaking_courses), encoding="utf-8", newline="\n")
    print("Built 5 listening + 5 speaking formal courses, 5 study packs, and 138 audio text items.")


if __name__ == "__main__":
    main()
