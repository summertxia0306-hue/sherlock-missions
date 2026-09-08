# -*- coding: utf-8 -*-
"""Build the approved 4A Unit 1 p7-p14 D06-D10 formal package."""
from __future__ import annotations

import hashlib
import json
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
DRAFT_OUT = ROOT / "content" / "drafts" / "4A-T1-W01-UNIT1"
CHILD_LISTENING_OUT = DRAFT_OUT / "child" / "listening"
CHILD_SPEAKING_OUT = DRAFT_OUT / "child" / "speaking"
DOCS_OUT = ROOT / "docs" / "course-batches"


DAY_META = {
    6: {
        "lesson": 6,
        "title": "四上·第6课｜Unit 1校园场所·我喜欢的地方",
        "scope": "4A Unit 1 p7-p9",
        "planned_difficulty": "L1",
        "json_difficulty": "L1",
        "listening_minutes": 12,
        "speaking_minutes": 8,
        "focus": "校园场所、场所与活动直接对应、表达喜欢",
        "max_plays": [2, 2, 2, 2, 3],
    },
    7: {
        "lesson": 7,
        "title": "四上·第7课｜Unit 1寻找同伴·在哪里见面",
        "scope": "4A Unit 1 p7-p10",
        "planned_difficulty": "L1+",
        "json_difficulty": "L1",
        "listening_minutes": 14,
        "speaking_minutes": 8,
        "focus": "寻找同伴、项目对话、选择见面地点",
        "max_plays": [2, 2, 2, 2, 3],
    },
    8: {
        "lesson": 8,
        "title": "四上·第8课｜Unit 1人物地点·连续对话",
        "scope": "4A Unit 1 p7-p11",
        "planned_difficulty": "L2",
        "json_difficulty": "L2",
        "listening_minutes": 17,
        "speaking_minutes": 8,
        "focus": "人物地点对应、连续对话、have no与do not have any",
        "max_plays": [2, 2, 2, 2, 3],
    },
    9: {
        "lesson": 9,
        "title": "四上·第9课｜Unit 1竹子学校·阅读整合",
        "scope": "4A Unit 1 p7-p13",
        "planned_difficulty": "L2+",
        "json_difficulty": "L2",
        "listening_minutes": 21,
        "speaking_minutes": 8,
        "focus": "竹子学校、建筑特点、跨句提取与整合",
        "max_plays": [1, 2, 2, 2, 3],
    },
    10: {
        "lesson": 10,
        "title": "四上·第10课｜Unit 1我最喜欢的校园地点·综合",
        "scope": "4A Unit 1 p7-p14",
        "planned_difficulty": "L3",
        "json_difficulty": "L3",
        "listening_minutes": 25,
        "speaking_minutes": 8,
        "focus": "Unit 1周综合、最喜欢的校园地点、稳定完整输出",
        "max_plays": [1, 1, 2, 2, 3],
    },
}


LISTENING_DATA = {
    6: {
        "words": [
            word("school building", ["school building", "sports field", "art room"], 0, a("p7-p8", "校园场所直接识别")),
            word("library", ["classroom", "library", "hall"], 1, a("p7-p8", "校园场所直接识别")),
            word("sports field", ["computer room", "sports field", "school building"], 1, a("p7-p8", "校园场所直接识别")),
            word("art room", ["hall", "classroom", "art room"], 2, c("p7-p8", "听音选词与校园场所辨别")),
        ],
        "sentences": [
            sentence("In the classroom I study.", "In the classroom I study.", "same", a("p9", "场所与活动对应")),
            sentence("On the sports field I play.", "On the sports field I play.", "same", a("p9", "场所与活动对应")),
            sentence("In the hall I study.", "In the hall I sing for all.", "different", a("p9", "相近场所活动辨别")),
            sentence("The library is the best of all.", "The library is the best of all.", "same", a("p9", "喜欢的校园场所")),
        ],
        "responses": [
            response("Where do you study?", ["In the classroom.", "On the sports field.", "In the hall."], 0, a("p9", "场所活动问答")),
            response("Where do you play?", ["In the library.", "On the sports field.", "In the computer room."], 1, c("p8-p9", "听问句选答语与地点辨别")),
            response("Where do you sing for all?", ["In the hall.", "In the classroom.", "In the art room."], 0, a("p8-p9", "场所活动问答")),
            response("Which place is the best of all in the rhyme?", ["The library.", "The classroom.", "The school building."], 0, a("p9", "韵文信息提取")),
        ],
        "dialogues": [
            dialogue([["f", "I like my school."], ["m", "It is lovely and cool."]], "What do they like?", ["Their school.", "The sports field only.", "The computer room only."], 0, a("p9", "两轮直接取信息")),
            dialogue([["f", "Where do you study?"], ["m", "In the classroom."]], "Where does the boy study?", ["In the classroom.", "In the hall.", "In the library."], 0, a("p9", "两轮场所活动对应")),
            dialogue([["m", "I play on the sports field."], ["f", "We do sports there every day."]], "What do they do there?", ["They study.", "They do sports.", "They sing."], 1, a("p9", "两轮活动提取")),
            dialogue([["f", "I like the sports field best."], ["m", "We play basketball there."]], "Which place does the girl like best?", ["The hall.", "The sports field.", "The library."], 1, a("p9", "教材示例复现")),
        ],
        "passage": "I like my school. It is lovely and cool. In the classroom I study. We always keep it tidy. On the sports field I play. We do sports there every day. In the hall I sing for all. The library is the best of all.",
        "statements": [
            passage_statement("The school is lovely and cool.", True, a("p9", "韵文直接信息")),
            passage_statement("The speaker studies in the hall.", False, a("p9", "场所活动辨别")),
            passage_statement("They do sports on the sports field every day.", True, a("p9", "场所活动提取")),
            passage_statement("The library is the best of all.", True, a("p9", "喜欢信息提取")),
        ],
    },
    7: {
        "words": [
            word("project", ["project", "library", "classroom"], 0, a("p10", "项目关键词")),
            word("school history", ["sports field", "school history", "computer room"], 1, a("p10", "项目主题短语")),
            word("ground floor", ["ground floor", "sports field", "school building"], 0, a("p10", "楼层信息")),
            word("computer room", ["classroom", "computer room", "library"], 1, c("p8-p10", "听音选词与相似房间辨别")),
        ],
        "sentences": [
            sentence("Shenshen and Minmin begin with their project.", "Shenshen and Minmin begin with their project.", "same", a("p10", "项目人物")),
            sentence("James is in the library.", "James is in the library.", "same", a("p10", "人物地点对应")),
            sentence("Xiaopu is in the computer room.", "Xiaopu is likely on the sports field.", "different", a("p10", "人物地点辨别")),
            sentence("The computer room is on the ground floor.", "The computer room is on the ground floor.", "same", a("p10", "见面地点信息")),
        ],
        "responses": [
            response("Shall we begin with our project?", ["Sure.", "In the library.", "On the ground floor."], 0, a("p10", "教材对话回应")),
            response("Where is James?", ["In the library.", "On the sports field.", "In the hall."], 0, c("p10", "听问句选答语与人物地点对应")),
            response("Where is Xiaopu likely to be?", ["In the classroom.", "On the sports field.", "In the art room."], 1, a("p10", "根据活动推断地点")),
            response("Where will the group meet?", ["In the computer room.", "In the hall.", "In the library."], 0, a("p10", "见面地点提取")),
        ],
        "dialogues": [
            dialogue([["f", "Shall we begin with our project?"], ["m", "Sure. But where are James and Xiaopu?"]], "What are they going to begin?", ["Their project.", "Their sports.", "Their song."], 0, a("p10", "两轮信息提取")),
            dialogue([["f", "Where is James?"], ["m", "He is in the library."]], "Where is James?", ["In the library.", "On the sports field.", "In the classroom."], 0, a("p10", "人物地点对应")),
            dialogue([["f", "Xiaopu likes playing football."], ["m", "He is likely on the sports field."]], "Why is Xiaopu likely there?", ["He likes playing football.", "He reads books there.", "He studies there."], 0, a("p10", "跨句原因提取")),
            dialogue([["f", "How about the computer room?"], ["m", "Sure. Let us meet there then."]], "Where will they meet?", ["In the classroom.", "In the computer room.", "In the library."], 1, a("p10", "指代与见面地点")),
        ],
        "passage": "Shenshen and Minmin begin with their school history project. James is in the library. Xiaopu likes playing football, so he is likely on the sports field. The classroom has no computers. The computer room is on the ground floor. They will meet there.",
        "statements": [
            passage_statement("The project is about school history.", True, a("p10", "项目主题")),
            passage_statement("James is on the sports field.", False, a("p10", "人物地点辨别")),
            passage_statement("Xiaopu likes playing football.", True, a("p10", "人物活动")),
            passage_statement("They will meet in the computer room.", True, a("p10", "跨句见面地点")),
        ],
    },
    8: {
        "words": [
            word("classroom", ["classroom", "computer room", "music room"], 0, a("p8-p11", "相似房间辨别")),
            word("second floor", ["ground floor", "second floor", "sports field"], 1, a("p11", "楼层选项辨别")),
            word("has no computers", ["has no computers", "has three floors", "has no walls"], 0, a("p10-p11", "否定结构听辨")),
            word("does not have any computers", ["has no computers", "does not have any computers", "has many computers"], 1, c("p10-p11", "听音选词与等义表达辨别")),
        ],
        "sentences": [
            sentence("The classroom has no computers.", "The classroom has no computers.", "same", a("p10-p11", "教材规则原句")),
            sentence("The classroom has no computers.", "The classroom does not have any computers.", "same", a("p11", "等义表达")),
            sentence("The computer room is on the second floor.", "The computer room is on the ground floor.", "different", a("p10-p11", "楼层干扰")),
            sentence("James is in the library and Xiaopu is likely on the sports field.", "James is in the library and Xiaopu is likely on the sports field.", "same", a("p10-p11", "双人物信息整合")),
        ],
        "responses": [
            response("Where is Xiaopu likely to be?", ["On the sports field.", "In the library.", "In the classroom."], 0, a("p10-p11", "人物地点匹配")),
            response("Where is James?", ["In the computer room.", "In the library.", "On the sports field."], 1, c("p10-p11", "听问句选答语与人物信息对应")),
            response("Does the classroom have any computers?", ["No, it does not.", "Yes, it does.", "It has three floors."], 0, a("p10-p11", "否定事实回应")),
            response("Where will Minmin's group meet?", ["In the computer room on the ground floor.", "In the classroom on the ground floor.", "In the library on the second floor."], 0, a("p10-p11", "地点与楼层整合")),
        ],
        "dialogues": [
            dialogue([["f", "Where are James and Xiaopu?"], ["m", "James is in the library."], ["f", "Xiaopu is likely on the sports field."]], "Who is in the library?", ["James.", "Xiaopu.", "Minmin."], 0, a("p10-p11", "三轮人物地点对应")),
            dialogue([["f", "Shall we meet in the classroom?"], ["m", "The classroom has no computers."], ["f", "How about the computer room?"]], "Why do they not choose the classroom?", ["It has no computers.", "It has no walls.", "It is on the second floor."], 0, a("p10-p11", "三轮跨句原因")),
            dialogue([["m", "Where is the computer room?"], ["f", "It is on the ground floor."], ["m", "Let us meet there then."]], "Where will they meet?", ["In the computer room.", "In the hall.", "On the sports field."], 0, a("p10-p11", "指代与地点整合")),
            dialogue([["f", "Xiaopu likes playing football."], ["m", "He is likely on the sports field."], ["f", "James is in the library."], ["m", "Let us look for them."]], "Which two places should they go to?", ["The sports field and the library.", "The classroom and the hall.", "The art room and the computer room."], 0, a("p10-p11", "四轮双地点整合")),
        ],
        "passage": "Minmin's group begins a school history project. James is in the library. Xiaopu likes playing football and is likely on the sports field. The group needs computers. The classroom has no computers. It does not have any computers. The computer room is on the ground floor, so they will meet there.",
        "statements": [
            passage_statement("James is in the library.", True, a("p10-p11", "人物地点")),
            passage_statement("Xiaopu is likely in the art room.", False, a("p10-p11", "人物地点干扰")),
            passage_statement("The classroom does not have any computers.", True, a("p11", "等义否定事实")),
            passage_statement("The group will meet on the second floor.", False, a("p10-p11", "跨句地点楼层整合")),
        ],
    },
    9: {
        "words": [
            word("bamboo", ["bamboo", "umbrella", "wall"], 0, a("p12-p13", "竹子学校关键词")),
            word("walls", ["floors", "walls", "classrooms"], 1, a("p12-p13", "建筑部位辨别")),
            word("umbrellas", ["buildings", "umbrellas", "computer rooms"], 1, a("p12", "外形比喻")),
            word("three floors", ["three floors", "ground floor", "school history"], 0, a("p12", "建筑楼层信息")),
            word("music room", ["computer room", "art room", "music room"], 2, c("p12", "听音选词与功能房辨别")),
        ],
        "sentences": [
            sentence("All the school buildings are made of bamboo.", "All the school buildings are made of bamboo.", "same", a("p12-p13", "建筑材料")),
            sentence("The bamboo buildings have no walls.", "The bamboo buildings do not have any walls.", "same", a("p11-p12", "等义否定表达")),
            sentence("The buildings look like boats.", "The buildings look like big umbrellas.", "different", a("p12", "建筑外形辨别")),
            sentence("Each building has three floors.", "Each building has three floors.", "same", a("p12", "楼层数量")),
            sentence("Students learn and play in bamboo classrooms and special rooms.", "Students learn and play in bamboo classrooms and special rooms.", "same", a("p12", "跨句活动概括")),
        ],
        "responses": [
            response("What are all the school buildings made of?", ["Bamboo.", "Walls.", "Umbrellas."], 0, a("p12-p13", "材料问答")),
            response("Do the bamboo buildings have any walls?", ["No, they do not.", "Yes, they do.", "They have three walls."], 0, a("p11-p12", "否定事实回应")),
            response("What do the buildings look like?", ["Big umbrellas.", "Boats.", "Computer rooms."], 0, c("p12", "听问句选答语与外形辨别")),
            response("How many floors does each building have?", ["One.", "Two.", "Three."], 2, a("p12", "数字信息提取")),
            response("Where do students learn and play?", ["In bamboo classrooms and special rooms.", "Only on the sports field.", "Only in the library."], 0, a("p12", "场所活动整合")),
        ],
        "dialogues": [
            dialogue([["f", "This is Green School Bali."], ["m", "What is special about it?"], ["f", "All the school buildings are made of bamboo."]], "What makes the school special?", ["Its bamboo buildings.", "Its boats.", "Its desks."], 0, a("p12-p13", "三轮建筑材料提取")),
            dialogue([["m", "Do the buildings have walls?"], ["f", "No, they do not have any walls."], ["m", "They look like big umbrellas."]], "What do the buildings not have?", ["Walls.", "Floors.", "Classrooms."], 0, a("p11-p12", "三轮否定信息")),
            dialogue([["f", "How many floors does each building have?"], ["m", "Three floors."], ["f", "The floors are made of bamboo too."]], "What are the floors made of?", ["Bamboo.", "Walls.", "Umbrellas."], 0, a("p12-p13", "跨句楼层材料")),
            dialogue([["m", "Where do students learn?"], ["f", "In bamboo classrooms and computer rooms."], ["m", "They also use music rooms and art rooms."]], "Which room is not named?", ["The hall.", "The music room.", "The art room."], 0, a("p12", "多地点信息筛选")),
            dialogue([["f", "The buildings have no walls."], ["m", "They look like big umbrellas."], ["f", "Each building has three floors."], ["m", "That is a special school."]], "How many features are given before the last sentence?", ["One.", "Two.", "Three."], 2, a("p12", "四轮信息计数")),
        ],
        "passage": "Green School Bali is special. All the school buildings are made of bamboo. The bamboo buildings have no walls. They do not have any walls, and they look like big umbrellas. Each building has three floors. The floors are made of bamboo too. Students learn and play in bamboo classrooms, computer rooms, music rooms and art rooms.",
        "statements": [
            passage_statement("Green School Bali has bamboo school buildings.", True, a("p12-p13", "学校材料概括")),
            passage_statement("The bamboo buildings have many walls.", False, a("p12", "否定信息辨别")),
            passage_statement("The buildings look like big umbrellas.", True, a("p12", "建筑外形")),
            passage_statement("Each building has two floors.", False, a("p12", "数字信息辨别")),
            passage_statement("Students use computer rooms, music rooms and art rooms.", True, a("p12", "跨句功能房整合")),
        ],
    },
    10: {
        "words": [
            word("favourite place", ["favourite place", "school history", "ground floor"], 0, a("p9-p14", "项目主题听辨")),
            word("looks like a boat", ["looks like a boat", "looks like an umbrella", "has three floors"], 0, a("p14", "图书馆外形")),
            word("chairs and desks", ["walls and floors", "chairs and desks", "books and computers"], 1, a("p14", "室内物品")),
            word("read many interesting books", ["read many interesting books", "play basketball every day", "sing for all"], 0, a("p9-p14", "场所活动辨别")),
            word("library", ["library", "classroom", "computer room"], 0, c("p7-p14", "听音选词与相似场所辨别")),
        ],
        "sentences": [
            sentence("The library is on the ground floor.", "The library is on the ground floor.", "same", a("p14", "图书馆位置")),
            sentence("The library looks like a big umbrella.", "The library looks like a boat.", "different", a("p12-p14", "相似外形干扰")),
            sentence("The library has no chairs or desks.", "The library does not have any chairs or desks.", "same", a("p11-p14", "等义否定表达")),
            sentence("In the library, I read many interesting books.", "In the library, I read many interesting books.", "same", a("p14", "图书馆活动")),
            sentence("The bamboo buildings have three floors and no walls.", "The bamboo buildings have three floors and no walls.", "same", a("p12-p13", "双特征整合")),
        ],
        "responses": [
            response("Which place do you like best in the example?", ["The library.", "The hall.", "The sports field."], 0, a("p14", "最喜欢的场所")),
            response("Where is the library?", ["On the ground floor.", "On the second floor.", "On the sports field."], 0, c("p11-p14", "听问句选答语与楼层辨别")),
            response("What does the library look like?", ["A boat.", "A big umbrella.", "A classroom."], 0, a("p14", "图书馆外形")),
            response("What does the library not have?", ["Any chairs or desks.", "Any books.", "Any floors."], 0, a("p14", "否定信息提取")),
            response("What do you do in the library?", ["I read many interesting books.", "I play basketball.", "I sing for all."], 0, a("p9-p14", "场所活动问答")),
        ],
        "dialogues": [
            dialogue([["f", "Which place do you like best?"], ["m", "I like the library best."], ["f", "Where is it?"], ["m", "It is on the ground floor."]], "Which place does the boy like best?", ["The library.", "The hall.", "The sports field."], 0, a("p14", "四轮喜好地点整合")),
            dialogue([["m", "What is special about the library?"], ["f", "It looks like a boat."], ["m", "Does it have chairs and desks?"], ["f", "No, it does not."]], "Which two features are given?", ["It looks like a boat and has no chairs or desks.", "It looks like an umbrella and has three floors.", "It is a hall and has computers."], 0, a("p11-p14", "四轮双特征整合")),
            dialogue([["f", "I study in the classroom."], ["m", "I play on the sports field."], ["f", "I sing in the hall."], ["m", "I read in the library."]], "Where does the boy read?", ["In the library.", "In the classroom.", "In the hall."], 0, a("p9-p14", "人物活动对应")),
            dialogue([["m", "The bamboo school buildings have no walls."], ["f", "They look like big umbrellas."], ["m", "Our library looks like a boat."], ["f", "Both places are special."]], "Which place looks like a boat?", ["The library.", "The bamboo buildings.", "The sports field."], 0, a("p12-p14", "相似外形跨句辨别")),
            dialogue([["f", "James is in the library."], ["m", "Xiaopu is on the sports field."], ["f", "The group will meet in the computer room."], ["m", "It is on the ground floor."]], "Where will the group meet?", ["In the computer room.", "In the library.", "On the sports field."], 0, a("p10-p14", "人物地点与目的地整合")),
        ],
        "passage": "I like the library in my school best. It is on the ground floor. It is very special and looks like a boat. The room does not have any chairs or desks. In the library, I read many interesting books. I also like our classroom, hall, computer room, art room and sports field. In the classroom I study, on the sports field I play, and in the hall I sing for all.",
        "statements": [
            passage_statement("The speaker's favourite place is the library.", True, a("p14", "最喜欢的场所")),
            passage_statement("The library is on the second floor.", False, a("p11-p14", "楼层信息干扰")),
            passage_statement("The library looks like a boat.", True, a("p14", "场所外形")),
            passage_statement("The library has chairs and desks.", False, a("p14", "否定信息")),
            passage_statement("The speaker studies, plays, sings and reads in different school places.", True, a("p9-p14", "跨句活动整合")),
        ],
    },
}


SPEAKING_DATA = {
    6: [
        ("repeat", "I like my school.", "", "", a("p9", "表达喜欢")),
        ("repeat", "It is lovely and cool.", "", "", a("p9", "描述学校")),
        ("repeat", "In the classroom I study.", "", "", a("p9", "场所活动")),
        ("repeat", "On the sports field I play.", "", "", a("p9", "场所活动")),
        ("repeat", "In the hall I sing for all.", "", "", a("p9", "场所活动")),
        ("repeat", "The library is the best of all.", "", "", a("p9", "表达喜欢")),
        ("qa", "Where do you study?", "In the classroom.", "回答在哪里学习。", c("p9", "听问句后准确回应")),
        ("qa", "Where do you play?", "On the sports field.", "回答在哪里玩或做运动。", a("p9", "场所活动问答")),
    ],
    7: [
        ("repeat", "Shall we begin with our project?", "", "", a("p10", "项目对话")),
        ("repeat", "Sure. But where are James and Xiaopu?", "", "", a("p10", "寻找同伴")),
        ("repeat", "James is in the library.", "", "", a("p10", "人物地点")),
        ("repeat", "Xiaopu is likely on the sports field.", "", "", a("p10", "人物地点推断")),
        ("repeat", "How about the computer room?", "", "", a("p10", "提议见面地点")),
        ("repeat", "Sure. Let us meet there then.", "", "", a("p10", "接受提议")),
        ("qa", "Where is James?", "He is in the library.", "用完整句回答James在哪里。", c("p10", "听问句后人物地点对应")),
        ("qa", "Where will the group meet?", "They will meet in the computer room.", "用完整句回答小组在哪里见面。", a("p10", "见面地点问答")),
    ],
    8: [
        ("repeat", "The classroom has no computers.", "", "", a("p10-p11", "否定结构")),
        ("repeat", "The classroom does not have any computers.", "", "", a("p11", "等义否定表达")),
        ("repeat", "James is in the library.", "", "", a("p10-p11", "人物地点")),
        ("repeat", "Xiaopu is likely on the sports field.", "", "", a("p10-p11", "人物地点推断")),
        ("repeat", "The computer room is on the ground floor.", "", "", a("p10-p11", "地点与楼层")),
        ("repeat", "Let us meet in the computer room then.", "", "", a("p10-p11", "连续对话输出")),
        ("qa", "Does the classroom have any computers?", "No, it does not.", "根据教材事实作否定回答。", c("p11", "听问句后准确回应")),
        ("qa", "Where will Minmin's group meet?", "They will meet in the computer room on the ground floor.", "同时说出房间和楼层。", a("p10-p11", "跨句地点整合")),
    ],
    9: [
        ("repeat", "All the school buildings are made of bamboo.", "", "", a("p12-p13", "建筑材料")),
        ("repeat", "These bamboo buildings have no walls.", "", "", a("p11-p12", "否定结构")),
        ("repeat", "They do not have any walls.", "", "", a("p11-p12", "等义否定表达")),
        ("repeat", "They look like big umbrellas.", "", "", a("p12", "建筑外形")),
        ("repeat", "Each building has three floors.", "", "", a("p12", "建筑楼层")),
        ("repeat", "Students learn and play in bamboo classrooms.", "", "", a("p12", "场所活动")),
        ("qa", "What are the school buildings made of?", "They are made of bamboo.", "用完整句回答建筑材料。", c("p12-p13", "听问句后材料回应")),
        ("qa", "What do the buildings look like?", "They look like big umbrellas.", "用完整句回答建筑外形。", a("p12", "建筑外形问答")),
    ],
    10: [
        ("repeat", "I like the library in my school best.", "", "", a("p14", "表达最喜欢的场所")),
        ("repeat", "It is on the ground floor.", "", "", a("p14", "地点楼层")),
        ("repeat", "It is very special and looks like a boat.", "", "", a("p14", "场所外形")),
        ("repeat", "The room does not have any chairs or desks.", "", "", a("p14", "室内否定信息")),
        ("repeat", "In the library, I read many interesting books.", "", "", a("p14", "场所活动")),
        ("repeat", "I like my school because every place is special.", "", "", a("p7-p14", "同语境综合输出")),
        ("qa", "Where is the library?", "It is on the ground floor.", "用完整句回答图书馆楼层。", c("p11-p14", "听问句后楼层辨别")),
        ("qa", "What do you do in the library?", "I read many interesting books in the library.", "用完整句回答在图书馆做什么。", a("p14", "稳定完整输出")),
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
        "week": 2,
        "day": day - 5,
        "course_type": "weekly_test" if day == 10 else "training",
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
        "week": 2,
        "day": day - 5,
        "course_type": "weekly_review" if day == 10 else "training",
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
            for day, listening, speaking in zip(range(6, 11), listening_courses, speaking_courses)
        ],
    }


def build_mapping_doc(listening_courses, speaking_courses):
    lines = [
        "# 4A 新教材 Unit 1 D06–D10 教材与课程映射",
        "",
        "> formal发布稿。教材事实源为确认版教材逐页转录，范围严格为Unit 1 p7–14。",
        "",
        "| 课次 | pair / study pack | 听力 | 口语 | 教材范围 | 难度 | 题量 | 总时长 | 重点 |",
        "|---|---|---|---|---|---|---:|---:|---|",
    ]
    for day, listening, speaking in zip(range(6, 11), listening_courses, speaking_courses):
        meta = DAY_META[day]
        count = sum(len(section["questions"]) for section in listening["sections"])
        lines.append(f"| 第{day}课 | {listening['pair_id']} | {listening['course_id']} | {speaking['course_id']} | {meta['scope']} | {meta['planned_difficulty']}（JSON {meta['json_difficulty']}） | {count}+8 | 约{meta['listening_minutes'] + meta['speaking_minutes']}分钟 | {meta['focus']} |")
    lines += [
        "",
        "## 开放规则",
        "",
        "- 2026-09-08家长确认：课程完成后默认formal开放，不再按学校逐页设置发布闸门。",
        "- 夏洛恪与家长按实际进度从推荐课开始逐课完成；家长负责提醒新的教材进度。",
        "- 全批不进入Unit 2，不制造test或formal学习记录。",
        "",
        "## A主线与C微调",
        "",
        "- 150题中A主线135题、C微调15题；C占10%。",
        "- 每门听力2道C题：1道听音选词、1道听问句选答语；每门口语1道C题：QA。",
        "- C只提高相似场所、人物地点和信息辨别质量，语言材料仍取Unit 1 p7–14，不作未掌握结论。",
        "",
    ]
    return "\n".join(lines)


def build_parent_doc(listening_courses, speaking_courses):
    lines = [
        "# 4A 新教材 Unit 1 D06–D10 家长版答案、原文与口语目标句",
        "",
        "> 家长专用。不得作为儿童公开副本；课程为formal发布稿。",
        "",
    ]
    for day, listening, speaking in zip(range(6, 11), listening_courses, speaking_courses):
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
    listening_courses = [build_listening(day) for day in range(6, 11)]
    speaking_courses = [build_speaking(day) for day in range(6, 11)]
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
    (DOCS_OUT / "2026-09-08-4A-Unit1-D06-D10教材与课程映射.md").write_text(build_mapping_doc(listening_courses, speaking_courses), encoding="utf-8", newline="\n")
    (DOCS_OUT / "2026-09-08-4A-Unit1-D06-D10家长版答案原文.md").write_text(build_parent_doc(listening_courses, speaking_courses), encoding="utf-8", newline="\n")
    print("Built 5 listening + 5 speaking formal courses, 5 study packs, and 138 audio text items.")


if __name__ == "__main__":
    main()
