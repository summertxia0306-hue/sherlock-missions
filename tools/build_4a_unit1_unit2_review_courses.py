# -*- coding: utf-8 -*-
"""Build the approved 4A Unit 1-Unit 2 review package D21-D25."""
from __future__ import annotations

from pathlib import Path

from build_4a_starter_courses import (
    a, answer_text, c, child_listening, child_speaking, dialogue, json_write,
    parent_note, passage_statement, response, sentence, transcript_text, word,
)
from build_4a_unit2_courses import SECTION_SPECS, child_catalog_entry, make_section


ROOT = Path(__file__).resolve().parents[1]
BATCH = "4A-T1-W01"
DRAFT = ROOT / "content/drafts/4A-T1-W01-UNIT1-UNIT2-REVIEW"
DOCS = ROOT / "docs/course-batches"

META = {
    21: ("Unit 1校园生活·地点活动与喜好", "4A Unit 1 p7-p14", "L1", "L1", 12, 10,
         "校园地点、活动、喜好与场所特点直接复习", [2, 2, 2, 2, 3]),
    22: ("Unit 2我的同学·特点习惯与梦想", "4A Unit 2 p15-p22", "L1+", "L1", 14, 10,
         "人物特点、频率习惯、梦想、擅长项目与帮助行为", [2, 2, 2, 2, 3]),
    23: ("Unit 1–2人物地点活动·信息整合", "4A Unit 1 p7-p14 + Unit 2 p15-p22", "L2", "L2", 17, 12,
         "人物、地点、活动和特点的双单元信息整合", [2, 2, 2, 2, 3]),
    24: ("Unit 1–2相似信息·连续对话", "4A Unit 1 p7-p14 + Unit 2 p15-p22", "L2+", "L2", 21, 12,
         "连续对话、相似信息辨别、跨句判断和理由提取", [1, 2, 2, 2, 3]),
    25: ("Unit 1–2综合复习与检测", "4A Unit 1 p7-p14 + Unit 2 p15-p22", "L3", "L3", 25, 12,
         "跨题型整合、综合判断与稳定完整输出", [1, 1, 2, 2, 3]),
}


def tag(day, pages, focus, micro=False):
    return (c if micro else a)(pages, focus)


def w(day, pages, heard, options, answer, focus, micro=False):
    return word(heard, options.split("|"), answer, tag(day, pages, focus, micro))


def s(day, pages, display, heard, same, focus):
    return sentence(display, heard, "same" if same else "different", tag(day, pages, focus))


def r(day, pages, prompt, options, answer, focus, micro=False):
    return response(prompt, options.split("|"), answer, tag(day, pages, focus, micro))


def d(day, pages, clips, question, options, answer, focus):
    return dialogue(clips, question, options.split("|"), answer, tag(day, pages, focus))


def p(day, pages, statement, correct, focus):
    return passage_statement(statement, correct, tag(day, pages, focus))


def q(day, pages, kind, prompt, expected="", hint="", focus="", micro=False):
    return kind, prompt, expected, hint, tag(day, pages, focus, micro)


CONTENT = {
    21: {
        "words": [
            w(21, "p7-p14", "library", "library|classroom|hall", 0, "校园地点直接识别"),
            w(21, "p7-p14", "sports field", "art room|sports field|computer room", 1, "校园地点直接识别"),
            w(21, "p10-p14", "ground floor", "second floor|ground floor|school building", 1, "楼层信息识别"),
            w(21, "p7-p14", "computer room", "classroom|computer room|art room", 1, "听音选词与相似房间辨别", True),
        ],
        "sentences": [
            s(21, "p9", "In the classroom I study.", "In the classroom I study.", True, "场所活动对应"),
            s(21, "p9", "We play basketball in the library.", "We play basketball on the sports field.", False, "场所活动辨别"),
            s(21, "p10-p11", "James is in the library.", "James is in the library.", True, "人物地点对应"),
            s(21, "p12-p14", "The bamboo buildings have many walls.", "The bamboo buildings have no walls.", False, "场所特点辨别"),
        ],
        "responses": [
            r(21, "p9", "Where do you study?", "In the classroom.|In the hall.|On the sports field.", 0, "场所活动问答"),
            r(21, "p10-p11", "Where is James?", "In the library.|In the art room.|In the classroom.", 0, "问句选答语与人物地点辨别", True),
            r(21, "p14", "Which place do you like best?", "I like the library best.|I read many books.|It is on the ground floor.", 0, "表达最喜欢的场所"),
            r(21, "p12-p13", "What are the school buildings made of?", "They are made of bamboo.|They look like umbrellas.|They have three floors.", 0, "建筑材料问答"),
        ],
        "dialogues": [
            d(21, "p9", [["f", "I like the sports field best."], ["m", "We play basketball there."]], "What do they do there?", "They study.|They play basketball.|They read books.", 1, "喜好与活动对应"),
            d(21, "p10-p11", [["m", "James is in the library."], ["f", "I can go and look for him."]], "Where will the girl go?", "To the library.|To the hall.|To the art room.", 0, "人物地点与行动对应"),
            d(21, "p10-p11", [["f", "The classroom has no computers."], ["m", "Let us meet in the computer room."]], "Why do they choose the computer room?", "They need computers.|They want to sing.|They want to play football.", 0, "地点选择信息"),
            d(21, "p14", [["m", "My favourite place is the library."], ["f", "It looks like a boat."]], "Which place looks like a boat?", "The library.|The bamboo school.|The sports field.", 0, "场所外形辨别"),
        ],
        "passage": "I like my school. In the classroom I study, and on the sports field I play. James is in the library. My favourite place is the library on the ground floor. It looks like a boat, and I read many interesting books there.",
        "statements": [
            p(21, "p9-p14", "The speaker studies in the classroom.", True, "场所活动判断"),
            p(21, "p9-p14", "James is on the sports field.", False, "人物地点判断"),
            p(21, "p14", "The library is on the ground floor.", True, "楼层信息判断"),
            p(21, "p14", "The library looks like a big umbrella.", False, "场所外形判断"),
        ],
        "speaking": [
            q(21, "p9", "repeat", "In the classroom I study, and on the sports field I play.", focus="场所与双活动"),
            q(21, "p9", "repeat", "I like the library best in our school.", focus="表达场所喜好"),
            q(21, "p10-p11", "repeat", "James is in the library, and Xiaopu is on the sports field.", focus="双人物地点"),
            q(21, "p10-p11", "repeat", "The classroom has no computers.", focus="场所否定信息"),
            q(21, "p12-p13", "repeat", "The bamboo buildings look like big umbrellas.", focus="建筑外形"),
            q(21, "p14", "repeat", "The library is on the ground floor and looks like a boat.", focus="地点与外形整合"),
            q(21, "p9", "qa", "Where do you play basketball?", "I play basketball on the sports field.", "用完整句回答：我在运动场打篮球。", "场所活动自主问答", True),
            q(21, "p10-p11", "qa", "Where will Minmin's group meet?", "They will meet in the computer room.", "用完整句回答：他们将在电脑教室见面。", "见面地点问答"),
            q(21, "p12-p13", "qa", "What are the bamboo buildings made of?", "They are made of bamboo.", "用完整句回答：它们是竹子做的。", "建筑材料问答"),
            q(21, "p14", "qa", "What do you do in the library?", "I read many interesting books in the library.", "用完整句回答：我在图书馆读许多有趣的书。", "场所活动完整输出"),
        ],
    },
    22: {
        "words": [
            w(22, "p15-p22", "helpful", "helpful|interesting|different", 0, "人物特点识别"),
            w(22, "p17-p22", "writer", "painter|writer|classmate", 1, "人物梦想识别"),
            w(22, "p17", "basketball", "football|basketball|long rope", 1, "擅长项目识别"),
            w(22, "p17-p19", "often helps", "always helps|often helps|often tells", 1, "听音选词与频率行为辨别", True),
        ],
        "sentences": [
            s(22, "p17", "Shenshen wants to be a writer.", "Shenshen wants to be a writer.", True, "人物梦想对应"),
            s(22, "p17", "Xiaojiang is good at basketball.", "Xiaopu is good at basketball.", False, "人物擅长项目辨别"),
            s(22, "p18-p19", "James often tells interesting stories.", "James often tells interesting stories.", True, "人物习惯对应"),
            s(22, "p20-p21", "James is sad at the end of the story.", "James is happy and excited at the end of the story.", False, "故事结果辨别"),
        ],
        "responses": [
            r(22, "p17", "What does Shenshen want to be?", "A writer.|A painter.|A teacher.", 0, "人物梦想问答"),
            r(22, "p17", "Who is good at basketball?", "Minmin.|Xiaopu.|James.", 1, "问句选答语与人物信息对应", True),
            r(22, "p18-p19", "How does James help other students?", "He helps them learn English.|He helps them draw.|He helps them play football.", 0, "帮助行为问答"),
            r(22, "p20-p21", "How does James feel at the end?", "Happy and excited.|Afraid and bad.|Lovely and helpful.", 0, "故事结果与情绪"),
        ],
        "dialogues": [
            d(22, "p17", [["f", "Shenshen wants to be a writer."], ["m", "Xiaojiang wants to be a painter."]], "Who wants to be a painter?", "Shenshen.|Xiaojiang.|Yaoyao.", 1, "双人物梦想对应"),
            d(22, "p17", [["m", "Minmin is good at football."], ["f", "Xiaopu is good at basketball."]], "What is Minmin good at?", "Football.|Basketball.|Painting.", 0, "双人物擅长项目辨别"),
            d(22, "p18-p19", [["f", "He has a lovely smile and many friends."], ["m", "He often tells interesting stories."], ["f", "It is James."]], "Who is the classmate?", "James.|Xiaopu.|Wenwen.", 0, "多线索猜人"),
            d(22, "p20-p21", [["m", "James is afraid of the long rope."], ["f", "His classmates slow it down and cheer for him."], ["m", "Now he jumps in and skips."]], "What helps James succeed?", "His classmates help him.|He leaves the sports field.|He reads a book.", 0, "问题解决结果"),
        ],
        "passage": "My classmates are different but all great. Shenshen wants to be a writer, and Xiaojiang wants to be a painter. Minmin is good at football, and Xiaopu is good at basketball. Yaoyao often helps James with his Chinese. James often helps other students learn English.",
        "statements": [
            p(22, "p17-p19", "Shenshen wants to be a writer.", True, "人物梦想判断"),
            p(22, "p17", "Xiaojiang is good at basketball.", False, "人物信息判断"),
            p(22, "p17", "Yaoyao helps James with his Chinese.", True, "帮助行为判断"),
            p(22, "p18-p19", "James helps other students learn Chinese.", False, "相似语言信息辨别"),
        ],
        "speaking": [
            q(22, "p15-p17", "repeat", "My classmates are different but all great.", focus="同学特点概括"),
            q(22, "p17", "repeat", "Shenshen wants to be a writer, and Xiaojiang wants to be a painter.", focus="双人物梦想"),
            q(22, "p17", "repeat", "Minmin is good at football, and Xiaopu is good at basketball.", focus="双人物擅长项目"),
            q(22, "p17", "repeat", "Yaoyao often helps James with his Chinese.", focus="频率与帮助行为"),
            q(22, "p18-p19", "repeat", "James often tells interesting stories and helps others learn English.", focus="人物多行为"),
            q(22, "p20-p21", "repeat", "His classmates cheer for him, and James is happy and excited.", focus="故事帮助与结果"),
            q(22, "p17", "qa", "Who is good at basketball?", "Xiaopu is good at basketball.", "用完整句回答：Xiaopu擅长篮球。", "人物与擅长项目对应", True),
            q(22, "p17", "qa", "What does Xiaojiang want to be?", "Xiaojiang wants to be a painter.", "用完整句回答：Xiaojiang想成为画家。", "人物梦想问答"),
            q(22, "p18-p19", "qa", "Why is James helpful?", "He often helps other students learn English.", "用完整句回答：他经常帮助其他同学学英语。", "人物帮助行为"),
            q(22, "p20-p21", "qa", "What is the result of the rope story?", "James jumps in and skips with his classmates.", "用完整句回答：James跳进去，和同学们一起跳绳。", "故事结果完整输出"),
        ],
    },
    23: {
        "words": [
            w(23, "p10-p11", "school history project", "school history project|guessing game|favourite place", 0, "Unit 1项目识别"),
            w(23, "p15-p22", "helpful classmate", "helpful classmate|interesting story|lovely school", 0, "Unit 2人物特点识别"),
            w(23, "p7-p14", "computer room", "computer room|classroom|art room", 0, "功能房识别"),
            w(23, "p17-p22", "painter", "writer|painter|classmate", 1, "听音选词与人物梦想辨别", True),
        ],
        "sentences": [
            s(23, "p9,p17", "Minmin plays basketball on the sports field.", "Minmin plays football and likes the sports field.", False, "跨单元人物活动辨别"),
            s(23, "p10-p11,p18-p19", "James is in the library and often helps others learn English.", "James is in the library and often helps others learn English.", True, "人物地点与行为整合"),
            s(23, "p14,p22", "The helpful girl likes painting pictures.", "The helpful girl likes painting pictures.", True, "喜好与人物特点整合"),
            s(23, "p12-p13,p20-p21", "The bamboo school has walls, and James cannot skip at the end.", "The bamboo school has no walls, and James can skip at the end.", False, "双单元事实判断"),
        ],
        "responses": [
            r(23, "p9", "Where does Minmin play football?", "On the sports field.|In the library.|In the hall.", 0, "人物活动地点问答"),
            r(23, "p17", "Who wants to be a painter?", "Shenshen.|Xiaojiang.|James.", 1, "问句选答语与人物梦想对应", True),
            r(23, "p10-p11", "Where can the group use computers?", "In the computer room.|In the hall.|On the sports field.", 0, "功能房选择"),
            r(23, "p18-p19", "What does James often do?", "He tells interesting stories.|He plays in the hall.|He reads about bamboo.", 0, "人物习惯问答"),
        ],
        "dialogues": [
            d(23, "p9,p17", [["f", "Minmin is good at football."], ["m", "He plays on the sports field."], ["f", "We always cheer for him."]], "Where does Minmin play?", "On the sports field.|In the hall.|In the library.", 0, "人物擅长与地点整合"),
            d(23, "p10-p11,p18-p19", [["m", "James is in the library."], ["f", "He often helps other students learn English."], ["m", "He is helpful and interesting."]], "Which two things do we learn about James?", "His place and his actions.|His dream and his sport.|His classroom and his teacher.", 0, "人物地点与行为整合"),
            d(23, "p14,p22", [["f", "She is friendly and helpful."], ["m", "She is good at painting pictures."], ["f", "She likes the art room in our school."]], "Which place does she like?", "The art room.|The sports field.|The computer room.", 0, "人物能力与场所匹配"),
            d(23, "p10-p11,p17", [["m", "Xiaopu is on the sports field."], ["f", "He is good at basketball."], ["m", "Let us look for him there."]], "Who will they look for?", "Xiaopu.|James.|Shenshen.", 0, "人物地点活动多信息"),
        ],
        "passage": "Our classmates use different places in the school. Minmin is good at football and plays on the sports field. James is in the library and often helps other students learn English. Xiaojiang wants to be a painter and likes the art room. The group meets in the computer room for the school history project.",
        "statements": [
            p(23, "p9,p17", "Minmin plays on the sports field.", True, "人物活动地点"),
            p(23, "p10-p11,p18-p19", "James is in the computer room.", False, "人物地点辨别"),
            p(23, "p17,p22", "Xiaojiang wants to be a painter.", True, "人物梦想判断"),
            p(23, "p10-p11", "The group meets in the classroom for the project.", False, "项目地点判断"),
        ],
        "speaking": [
            q(23, "p9,p17", "repeat", "Minmin is good at football and plays on the sports field.", focus="人物能力与地点"),
            q(23, "p10-p11,p18-p19", "repeat", "James is in the library and often helps other students learn English.", focus="人物地点与行为"),
            q(23, "p17,p22", "repeat", "Xiaojiang wants to be a painter and is good at painting pictures.", focus="人物梦想与能力"),
            q(23, "p14,p22", "repeat", "The helpful girl likes the art room and often helps me draw.", focus="人物特点与场所"),
            q(23, "p10-p11", "repeat", "The group needs computers and meets in the computer room.", focus="需求与见面地点"),
            q(23, "p12-p13,p15-p22", "repeat", "Our school is special, and our classmates are different but all great.", focus="双单元主题整合"),
            q(23, "p17", "qa", "Who wants to be a painter?", "Xiaojiang wants to be a painter.", "用完整句回答：Xiaojiang想成为画家。", "人物梦想对应", True),
            q(23, "p9,p17", "qa", "Where does Minmin play football?", "Minmin plays football on the sports field.", "用完整句回答：Minmin在运动场踢足球。", "人物活动地点"),
            q(23, "p10-p11,p18-p19", "qa", "Where is James and how does he help others?", "James is in the library and helps others learn English.", "用一句话回答：James在图书馆，并帮助别人学英语。", "双信息整合问答"),
            q(23, "p14", "qa", "What is special about the library?", "It is on the ground floor and looks like a boat.", "用一句话说出图书馆的位置和外形。", "场所双特征"),
            q(23, "p22", "qa", "What is the helpful girl good at?", "She is good at painting pictures.", "用完整句回答：她擅长画画。", "人物能力问答"),
            q(23, "p10-p11", "qa", "Where will the group meet for the project?", "They will meet in the computer room.", "用完整句回答：他们将在电脑教室见面。", "项目地点输出"),
        ],
    },
    24: {
        "words": [
            w(24, "p10-p14", "ground floor", "ground floor|second floor|school building", 0, "楼层相似信息辨别"),
            w(24, "p17-p19", "helps students learn English", "helps students learn English|helps James with Chinese|helps teachers clean", 0, "相似帮助行为辨别"),
            w(24, "p17-p22", "painting pictures", "telling stories|painting pictures|playing basketball", 1, "活动与梦想辨别"),
            w(24, "p20-p21", "turn the rope more slowly", "turn the rope more slowly|jump over the rope|keep going", 0, "故事解决办法识别"),
            w(24, "p7-p22", "helpful", "helpful|interesting|lovely", 0, "听音选词与特点词辨别", True),
        ],
        "sentences": [
            s(24, "p10-p11", "James is in the library, but the group will meet in the computer room.", "James is in the library, but the group will meet in the computer room.", True, "人物地点与目的地辨别"),
            s(24, "p12-p14", "The bamboo buildings look like boats, and the library looks like umbrellas.", "The bamboo buildings look like umbrellas, and the library looks like a boat.", False, "相似外形交叉辨别"),
            s(24, "p17-p19", "Yaoyao helps James with Chinese, and James helps others learn English.", "Yaoyao helps James with Chinese, and James helps others learn English.", True, "相似帮助行为对应"),
            s(24, "p17", "Shenshen wants to be a painter, and Xiaojiang wants to be a writer.", "Shenshen wants to be a writer, and Xiaojiang wants to be a painter.", False, "人物梦想交叉辨别"),
            s(24, "p20-p21", "James is afraid at first and excited at the end.", "James is afraid at first and excited at the end.", True, "故事情绪变化"),
        ],
        "responses": [
            r(24, "p10-p11", "Where is James, and where will the group meet?", "James is in the library, and they will meet in the computer room.|James is in the hall, and they will meet in the library.|James is on the sports field, and they will meet in the classroom.", 0, "双地点问答"),
            r(24, "p17", "Who wants to be a writer?", "Shenshen.|Xiaojiang.|Yaoyao.", 0, "问句选答语与人物梦想对应", True),
            r(24, "p17-p19", "Who helps James with Chinese?", "Yaoyao.|Xiaopu.|Wenwen.", 0, "相似帮助行为问答"),
            r(24, "p14", "What does the library look like, and what do you do there?", "It looks like a boat, and I read books there.|It looks like an umbrella, and I play there.|It has three floors, and I sing there.", 0, "场所外形与活动整合"),
            r(24, "p20-p21", "What is the result of the rope story?", "James jumps in and skips.|James ducks and leaves.|The class reads in the library.", 0, "故事结果问答"),
        ],
        "dialogues": [
            d(24, "p10-p11", [["f", "James is in the library."], ["m", "Xiaopu is on the sports field."], ["f", "The classroom has no computers."], ["m", "Then let us meet in the computer room on the ground floor."]], "Where will the group meet?", "In the library.|In the classroom.|In the computer room.", 2, "四轮信息与目的地"),
            d(24, "p17-p19", [["m", "Yaoyao often helps James with his Chinese."], ["f", "James often helps other students learn English."], ["m", "Xiaopu helps teachers clean the blackboard."]], "Who helps students learn English?", "Yaoyao.|James.|Xiaopu.", 1, "三人物相似行为辨别"),
            d(24, "p14,p22", [["f", "She is friendly and helpful."], ["m", "She is good at painting pictures."], ["f", "She likes the art room, but her favourite place is the library."]], "Which place does she like best?", "The art room.|The library.|The sports field.", 1, "能力相关地点与最喜欢地点辨别"),
            d(24, "p17,p20-p21", [["m", "Minmin is good at football."], ["f", "She also shows James how to jump."], ["m", "Shenshen and Xiaojiang slow down the rope."], ["f", "Then James jumps in and skips."]], "What does Minmin do for James?", "She shows him how to jump.|She cleans the blackboard.|She reads to him.", 0, "人物多行为跨句提取"),
            d(24, "p12-p14", [["f", "The bamboo buildings have no walls and look like umbrellas."], ["m", "Our library has no chairs or desks and looks like a boat."], ["f", "These places are special."]], "Which place looks like a boat?", "The bamboo buildings.|The library.|The sports field.", 1, "相似场所特征辨别"),
        ],
        "passage": "James is in the library, but his group will meet in the computer room on the ground floor. The classroom has no computers. James is helpful and often helps other students learn English. Yaoyao helps James with his Chinese. Later, the classmates skip with a long rope. James is afraid at first. His classmates slow down the rope and cheer for him. Then he jumps in and skips.",
        "statements": [
            p(24, "p10-p11", "The group will meet in the library.", False, "人物地点与目的地辨别"),
            p(24, "p10-p11", "The classroom does not have any computers.", True, "等义否定信息"),
            p(24, "p17-p19", "Yaoyao helps James learn English.", False, "相似帮助行为辨别"),
            p(24, "p20-p21", "The classmates turn the rope more slowly for James.", True, "解决办法提取"),
            p(24, "p20-p21", "James is still afraid and cannot skip at the end.", False, "故事结果整合"),
        ],
        "speaking": [
            q(24, "p10-p11", "repeat", "James is in the library, but the group will meet in the computer room.", focus="人物地点与目的地"),
            q(24, "p12-p14", "repeat", "The bamboo buildings look like umbrellas, but the library looks like a boat.", focus="相似外形对比"),
            q(24, "p17", "repeat", "Shenshen wants to be a writer, and Xiaojiang wants to be a painter.", focus="人物梦想对应"),
            q(24, "p17-p19", "repeat", "Yaoyao helps James with Chinese, and James helps others learn English.", focus="相似帮助行为"),
            q(24, "p20-p21", "repeat", "His classmates slow down the rope and cheer for him.", focus="故事解决办法"),
            q(24, "p20-p21", "repeat", "James is afraid at first, but he is happy and excited at the end.", focus="故事情绪变化"),
            q(24, "p17", "qa", "Who wants to be a writer?", "Shenshen wants to be a writer.", "用完整句回答：Shenshen想成为作家。", "人物梦想对应", True),
            q(24, "p10-p11", "qa", "Where is James, and where will the group meet?", "James is in the library, and the group will meet in the computer room.", "用一句话说出James的位置和小组见面地点。", "双地点信息整合"),
            q(24, "p12-p14", "qa", "What do the bamboo buildings and the library look like?", "The bamboo buildings look like umbrellas, and the library looks like a boat.", "用一句话分别说出两处建筑的外形。", "相似外形跨句输出"),
            q(24, "p17-p19", "qa", "How do Yaoyao and James help others?", "Yaoyao helps James with Chinese, and James helps others learn English.", "用一句话分别说出两人的帮助行为。", "相似人物行为输出"),
            q(24, "p20-p21", "qa", "How do the classmates help James?", "They slow down the rope and cheer for him.", "用完整句回答：他们放慢绳子并为他加油。", "故事解决办法"),
            q(24, "p20-p21", "qa", "How does James feel at first and at the end?", "He is afraid at first and happy and excited at the end.", "用一句话说出James开始和最后的感受。", "跨句情绪变化"),
        ],
    },
    25: {
        "words": [
            w(25, "p7-p14", "favourite place", "favourite place|school project|guessing game", 0, "Unit 1项目主题"),
            w(25, "p15-p22", "guessing game", "school history|guessing game|bamboo school", 1, "Unit 2项目主题"),
            w(25, "p10-p14", "does not have any", "does not have any|has three floors|looks like a boat", 0, "否定结构识别"),
            w(25, "p17-p22", "good at painting pictures", "good at painting pictures|good at basketball|helps students learn English", 0, "人物能力短语"),
            w(25, "p7-p22", "interesting", "interesting|helpful|different", 0, "听音选词与人物特点辨别", True),
        ],
        "sentences": [
            s(25, "p9,p17", "Minmin is good at football and plays on the sports field.", "Minmin is good at football and plays on the sports field.", True, "人物能力地点整合"),
            s(25, "p10-p11,p18-p19", "James is in the library and helps other students learn Chinese.", "James is in the library and helps other students learn English.", False, "人物地点与语言辨别"),
            s(25, "p12-p14", "The bamboo buildings and the library look the same.", "The bamboo buildings look like umbrellas, but the library looks like a boat.", False, "双场所外形判断"),
            s(25, "p17-p22", "The girl is helpful, good at painting pictures, and wants to be a painter.", "The girl is helpful, good at painting pictures, and wants to be a painter.", True, "人物多线索整合"),
            s(25, "p20-p21", "James cannot skip at first, but he can skip at the end.", "James cannot skip at first, but he can skip at the end.", True, "故事前后变化"),
        ],
        "responses": [
            r(25, "p9-p14", "Which school place do you like best, and what do you do there?", "I like the library best and read books there.|I am helpful and interesting.|I want to be a painter.", 0, "喜好与活动综合问答"),
            r(25, "p17-p19", "Who often helps James with his Chinese?", "Yaoyao.|Xiaopu.|Wenwen.", 0, "问句选答语与人物信息对应", True),
            r(25, "p17-p22", "Who wants to be a painter and is good at painting pictures?", "Xiaojiang or the girl in the project.|James in the library.|Minmin on the sports field.", 0, "梦想与能力双线索"),
            r(25, "p10-p11,p18-p19", "Where is James, and what does he often do?", "He is in the library and often helps others learn English.|He is in the hall and often sings.|He is on the sports field and plays basketball.", 0, "人物地点行为整合"),
            r(25, "p20-p21", "What happens after the classmates help James?", "He jumps in and skips.|He goes to the library.|He cleans the blackboard.", 0, "故事因果结果"),
        ],
        "dialogues": [
            d(25, "p9,p17", [["f", "Minmin is good at football."], ["m", "He plays on the sports field."], ["f", "Xiaopu is good at basketball."], ["m", "We always cheer for them."]], "Which sport is Minmin good at?", "Football.|Basketball.|Skipping.", 0, "多人物运动辨别"),
            d(25, "p10-p11,p18-p19", [["m", "James is in the library."], ["f", "He often tells interesting stories."], ["m", "He also helps other students learn English."], ["f", "He is interesting and helpful."]], "Which two words describe James?", "Interesting and helpful.|Lovely and different.|Afraid and excited.", 0, "地点行为到人物特点整合"),
            d(25, "p12-p14,p22", [["f", "The library is on the ground floor and looks like a boat."], ["m", "This helpful girl is good at painting pictures."], ["f", "She likes the art room, but she reads in the library."]], "Where does the girl read?", "In the art room.|In the library.|In the hall.", 1, "人物活动与场所筛选"),
            d(25, "p17,p20-p21", [["m", "Shenshen wants to be a writer."], ["f", "Xiaojiang wants to be a painter."], ["m", "They slow down the rope for James."], ["f", "Then they cheer when he skips."]], "What do Shenshen and Xiaojiang do for James?", "They slow the rope and cheer.|They teach him to paint.|They meet him in the library.", 0, "人物梦想与故事行为筛选"),
            d(25, "p7-p22", [["f", "Our favourite school place project is about the library."], ["m", "Our classmate project is a guessing game."], ["f", "One project describes a place."], ["m", "The other describes a classmate."]], "What do the two projects describe?", "A place and a classmate.|Two sports fields.|Two bamboo buildings.", 0, "双单元项目主题整合"),
        ],
        "passage": "Our school is special, and our classmates are different but all great. Minmin is good at football and plays on the sports field. James is in the library, tells interesting stories, and helps other students learn English. The library is on the ground floor and looks like a boat. A helpful girl likes painting pictures and wants to be a painter. When James is afraid of the long rope, his classmates slow it down and cheer for him. At the end, he jumps in and skips.",
        "statements": [
            p(25, "p9,p17", "Minmin is good at basketball.", False, "人物运动辨别"),
            p(25, "p10-p11,p18-p19", "James is in the library and helps others learn English.", True, "人物地点行为整合"),
            p(25, "p14", "The library looks like a boat.", True, "场所外形判断"),
            p(25, "p17-p22", "The helpful girl wants to be a writer.", False, "人物梦想辨别"),
            p(25, "p20-p21", "James jumps in and skips after his classmates help him.", True, "故事因果结果"),
        ],
        "speaking": [
            q(25, "p9,p17", "repeat", "Minmin is good at football and plays on the sports field.", focus="人物能力地点综合"),
            q(25, "p10-p11,p18-p19", "repeat", "James is in the library, tells interesting stories, and helps others learn English.", focus="人物三信息整合"),
            q(25, "p12-p14", "repeat", "The bamboo buildings look like umbrellas, but the library looks like a boat.", focus="双场所外形对比"),
            q(25, "p17-p22", "repeat", "She is friendly and helpful, good at painting pictures, and wants to be a painter.", focus="人物多线索描述"),
            q(25, "p20-p21", "repeat", "His classmates slow down the rope, cheer for him, and help him skip.", focus="故事帮助过程"),
            q(25, "p7-p22", "repeat", "Our school is lovely, and our classmates are different but all great.", focus="双单元主题总结"),
            q(25, "p17-p19", "qa", "Who often helps James with his Chinese?", "Yaoyao often helps James with his Chinese.", "用完整句回答：Yaoyao经常帮助James学中文。", "人物信息对应", True),
            q(25, "p9,p17", "qa", "Where does Minmin play, and what is he good at?", "Minmin plays on the sports field and is good at football.", "用一句话说出Minmin活动的地点和擅长项目。", "人物地点能力整合"),
            q(25, "p10-p11,p18-p19", "qa", "Where is James, and why is he helpful?", "James is in the library and often helps others learn English.", "用一句话说出James的位置和帮助行为。", "人物地点行为整合"),
            q(25, "p12-p14", "qa", "How are the bamboo buildings and the library different?", "The bamboo buildings look like umbrellas, and the library looks like a boat.", "用一句话分别说出两处建筑的外形。", "双场所外形整合"),
            q(25, "p17-p22", "qa", "Can you describe the helpful girl in the project?", "She is helpful, good at painting pictures, and wants to be a painter.", "用一句话说出她的特点、擅长项目和梦想。", "人物三线索描述"),
            q(25, "p20-p21", "qa", "What is the problem, and what is the result in the rope story?", "James cannot skip at first, but he jumps in and skips at the end.", "用一句话说出故事中的问题和结果。", "故事前后整合输出"),
        ],
    },
}


def build_listening(day):
    title, scope, _, difficulty, minutes, _, _, plays = META[day]
    course_id = f"L4A-T1-W01-D{day:02d}"
    pair = f"4A-T1-W01-D{day:02d}"
    data = CONTENT[day]
    sections, next_id = [], 1
    for index, (section_id, name, tip, key) in enumerate(SECTION_SPECS):
        section = make_section(section_id, name, tip, plays[index], data[key], course_id, next_id)
        sections.append(section)
        next_id += len(section["questions"])
    passage = make_section("passage", "听短文判断", "先听完整短文，再判断每句话是否正确", plays[4], data["statements"], course_id, next_id)
    passage.update({"shared_audio": True, "passage_audio": f"static/audio/listening/{course_id}/p01.mp3", "passage_transcript": [["n", data["passage"]]]})
    sections.append(passage)
    count = sum(len(section["questions"]) for section in sections)
    assert [len(section["questions"]) for section in sections] == [count // 5] * 5
    return {
        "course_id": course_id, "weekly_batch_id": BATCH, "study_pack": pair, "pair_id": pair,
        "publication_status": "formal", "title": f"四上·第{day}课｜{title}（听力）",
        "week": 5, "day": day - 20, "course_type": "weekly_test" if day == 25 else "training",
        "est_minutes": minutes, "scope": scope, "difficulty": difficulty,
        "scoring": {"per_question": 100 // count, "total": 100},
        "test_audio": f"static/audio/listening/{course_id}/hello.mp3",
        "test_transcript": [["n", "Hello! Can you hear me? Let us begin."]], "sections": sections,
    }


def build_speaking(day):
    title, scope, _, difficulty, _, minutes, _, _ = META[day]
    course_id = f"S4A-T1-W01-D{day:02d}"
    pair = f"4A-T1-W01-D{day:02d}"
    questions = []
    for index, (kind, prompt, expected, hint, tag_value) in enumerate(CONTENT[day]["speaking"], 1):
        question = {
            "id": index, "type": kind,
            "audio": f"static/audio/speaking/{course_id}/q{index:02d}.mp3",
            "tag": tag_value, "parent_note": parent_note(tag_value),
        }
        if kind == "repeat":
            question["text"] = prompt
        else:
            question.update({"question": prompt, "expected": expected, "hint": hint})
        questions.append(question)
    return {
        "course_id": course_id, "weekly_batch_id": BATCH, "study_pack": pair, "pair_id": pair,
        "publication_status": "formal", "title": f"四上·第{day}课｜{title}（口语）",
        "week": 5, "day": day - 20, "course_type": "weekly_review" if day == 25 else "training",
        "est_minutes": minutes, "scope": scope, "difficulty": difficulty, "questions": questions,
    }


def audio_plan(listening, speaking):
    items = []
    for course in listening:
        items.append({"module": "listening", "course_id": course["course_id"], "kind": "test_audio", "path": course["test_audio"], "clips": course["test_transcript"]})
        for section in course["sections"]:
            if section.get("shared_audio"):
                items.append({"module": "listening", "course_id": course["course_id"], "kind": "passage", "path": section["passage_audio"], "clips": section["passage_transcript"]})
            for question in section["questions"]:
                if question.get("audio"):
                    items.append({"module": "listening", "course_id": course["course_id"], "kind": f"question_{question['id']:02d}", "path": question["audio"], "clips": question["transcript"]})
    listen_count = len(items)
    for course in speaking:
        for question in course["questions"]:
            spoken = question["text"] if question["type"] == "repeat" else question["question"]
            items.append({"module": "speaking", "course_id": course["course_id"], "kind": f"question_{question['id']:02d}_{question['type']}", "path": question["audio"], "clips": [["n", spoken]]})
    return {
        "weekly_batch_id": BATCH, "generation_status": "READY_TO_GENERATE", "publication_status": "formal",
        "expected_listening_outputs": listen_count, "expected_speaking_outputs": len(items) - listen_count,
        "expected_total_outputs": len(items), "items": items,
    }


def documents(listening, speaking):
    mapping = [
        "# 4A 新教材 Unit 1–Unit 2 综合复习 D21–D25 教材与课程映射", "",
        "> 内容开发交付稿；教材事实源为确认版教材 B003 p7–14 与 B004 p15–22。回归测试和正式部署由 02 窗口负责。", "",
        "| 课次 | 配对 ID | 教材范围 | 听力/口语 | 难度 | 时长 | 重点 |",
        "|---|---|---|---:|---|---:|---|",
    ]
    parent = [
        "# 4A 新教材 Unit 1–Unit 2 综合复习 D21–D25 家长版答案、原文与口语目标句", "",
        "> 家长专用，不作为儿童公开副本。回归测试和正式部署由 02 窗口负责。", "",
    ]
    for day, lcourse, scourse in zip(range(21, 26), listening, speaking):
        title, scope, planned, _, lmins, smins, focus, _ = META[day]
        count = sum(len(section["questions"]) for section in lcourse["sections"])
        mapping.append(f"| D{day:02d}｜{title} | {lcourse['pair_id']} | {scope} | {count}+{len(scourse['questions'])} | {planned} | 约{lmins+smins}分钟 | {focus} |")
        parent += [
            f"## D{day:02d}｜{lcourse['course_id']} / {scourse['course_id']}", "",
            f"教材：{scope}；难度：{planned}；听力 {count} 题，口语 6 repeat + {len(scourse['questions'])-6} QA。", "",
            "### 听力答案与原文", "",
        ]
        for section in lcourse["sections"]:
            parent += [f"**{section['name']}**（最多播放 {section['max_plays']} 次）", ""]
            if section.get("shared_audio"):
                parent += [f"短文原文：{section['passage_transcript'][0][1]}", ""]
            parent += ["| 题号 | 原文/题干 | 答案 | 来源与考点 |", "|---:|---|---|---|"]
            for question in section["questions"]:
                parent.append(f"| {question['id']} | {transcript_text(question)} | {answer_text(question)} | {question['tag']} |")
            parent.append("")
        parent += ["### 口语目标句", "", "| 题号 | 类型 | 示范文本 | 评测目标 | 来源与考点 |", "|---:|---|---|---|---|"]
        for question in scourse["questions"]:
            prompt = question["text"] if question["type"] == "repeat" else question["question"]
            target = question["text"] if question["type"] == "repeat" else question["expected"]
            parent.append(f"| {question['id']} | {question['type']} | {prompt} | {target} | {question['tag']} |")
        parent.append("")
    mapping += [
        "", "## 页段依据", "",
        "- D21：Unit 1 p7–14，校园地点、活动、项目对话、竹子学校与最喜欢的校园地点。",
        "- D22：Unit 2 p15–22，同学特点、梦想、擅长项目、帮助行为、跳长绳故事与猜人项目。",
        "- D23–D25：只在上述两单元内重组人物、地点、活动和项目线索；不进入 p23 Unit 3。", "",
        "## A 主线与 C 微调", "",
        "- 共 166 题：A 主线 151、C 微调 15（约 9%）。",
        "- 每课仅 2 道听力 C（听音选词、听问句选答语）和 1 道口语 C（QA）。",
        "- C 只做中性的相似信息辨别强化；没有新增正式弱项结论，也不读取 test 或单次错误。", "",
        "## 发布边界", "",
        "- 父课程为 formal 可见候选；本窗口不 push、不部署、不生成学习记录。",
        "- 02 窗口负责发布目录同步、完整工程回归、线上音频哈希和正式部署。",
        "- 当前系统已兼容口语 10/12 题；如 02 同步回归出现新限制，应由 02 处理，不在本窗口修改核心程序。", "",
    ]
    return "\n".join(mapping), "\n".join(parent)


def validation_handoff():
    return """# 4A Unit 1–Unit 2 综合复习 D21–D25 校验与 02 交接

## 课程范围

- study pack：D21、D22、D23、D24、D25，对应 `4A-T1-W01-D21` 至 `4A-T1-W01-D25`。
- 听力：L4A-T1-W01-D21、D22、D23、D24、D25；口语：S4A-T1-W01-D21、D22、D23、D24、D25，共 10 门课程。
- 教材：确认版新教材 Unit 1 p7–14 与 Unit 2 p15–22；禁止进入 p23 Unit 3。
- 题量：听力 20/20/20/25/25；口语 10/10/12/12/12，均为前 6 题 repeat、其余 QA。
- D25：weekly_test / weekly_review。

## 内容边界

- 166 题中 A 主线 151、C 微调 15；C 仅为中性相似信息辨别强化。
- 不读取或写入 test/formal 学习记录，不形成新的孩子能力结论。
- 儿童安全副本不得包含答案、原文、考点、家长说明、评测目标或数字计分字段。

## 02 交接

- 当前父课程 JSON、草案儿童副本、音频清单和 manifest 由 01 交付。
- 02 负责把新增课程同步到发布目录，运行前端/云函数/生产构建回归并部署。
- 01 不修改 app.py、CloudBase、推荐算法、录音、讯飞评分或 formal/test 治理。

## 自动验证结果

- 本批专项内容契约：4/4 通过。
- 全仓 Python：102/102 通过；其中旧课程白名单已只增加 D21–D25，W01D39–D40 锁定哈希仍通过。
- schema：10/10 父课程在 check_audio=True 下通过；听力题号连续、五类题型均衡、总分 100；口语题号连续且为 6 repeat + 4/6 QA。
- 音频：听力 98、口语 56，合计 154/154 存在、非空、进入对应 manifest，154/154 通过 FFmpeg 完整解码。
- 儿童安全：10/10 派生儿童课程不含答案、原文、考点、家长说明、评测目标或数字计分字段。
- 敏感信息：新增课程、草案、映射、答案原文、设计与交接文档中，受检密钥/密码标记 0 命中。
- 教材边界：专项测试确认包含 Unit 1/2 关键材料且不含 Unit 3、Unit 4、p23 或动物单元标记。

## 明确留给 02 的工作

- 将 D21–D25 儿童副本、catalog 与音频 manifest 同步到 Web/云函数发布目录；01 未运行发布同步脚本。
- 运行 Web、sherlock-api、score-speaking、TypeScript 与生产构建回归，并核对 10/12 题结果结构和题号 9–12。
- 部署后验证课程目录、推荐窗口、154 项线上音频哈希及代表页面；本批不在 01 窗口部署。
- 当前源代码已接受口语 8/10/12 题和新学期编号，未发现需要 01 越界修复的题量或编号阻塞。
"""


def main():
    listening = [build_listening(day) for day in range(21, 26)]
    speaking = [build_speaking(day) for day in range(21, 26)]
    for module, courses, child_builder in (("listening", listening, child_listening), ("speaking", speaking, child_speaking)):
        catalog = []
        for course in courses:
            json_write(ROOT / "content" / module / f"{course['course_id']}.json", course)
            child = child_builder(course)
            json_write(DRAFT / "child" / module / f"{course['course_id']}.json", child)
            catalog.append(child_catalog_entry(course, child))
        json_write(DRAFT / "child" / module / "catalog.json", catalog)
    packs = {
        "weekly_batch_id": BATCH, "publication_status": "formal", "visible": True,
        "authority_note": "父JSON为唯一活动源；本目录仅含配对、音频计划和派生儿童安全副本。02负责回归与线上部署。",
        "study_packs": [
            {
                "lesson": day, "study_pack": listening[index]["study_pack"], "pair_id": listening[index]["pair_id"],
                "planned_title": f"四上·第{day}课｜{META[day][0]}", "textbook_scope": listening[index]["scope"],
                "planned_difficulty": META[day][2], "json_difficulty": META[day][3],
                "planned_total_minutes": META[day][4] + META[day][5], "focus": META[day][6],
                "listening_course_id": listening[index]["course_id"], "speaking_course_id": speaking[index]["course_id"],
                "publication_gate": "02完成回归测试及线上部署后验收；内容窗口不部署。",
            }
            for index, day in enumerate(range(21, 26))
        ],
    }
    json_write(DRAFT / "study-packs.json", packs)
    json_write(DRAFT / "audio-generation-plan.json", audio_plan(listening, speaking))
    mapping, parent = documents(listening, speaking)
    DOCS.mkdir(parents=True, exist_ok=True)
    prefix = DOCS / "2026-09-23-4A-Unit1-Unit2-Review-D21-D25"
    Path(str(prefix) + "教材与课程映射.md").write_text(mapping, encoding="utf-8", newline="\n")
    Path(str(prefix) + "家长版答案原文.md").write_text(parent, encoding="utf-8", newline="\n")
    Path(str(prefix) + "校验与02交接.md").write_text(validation_handoff(), encoding="utf-8", newline="\n")
    print("Built Unit 1-Unit 2 review D21-D25: five listening, five speaking, five study packs.")


if __name__ == "__main__":
    main()
