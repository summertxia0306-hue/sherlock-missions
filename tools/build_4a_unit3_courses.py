# -*- coding: utf-8 -*-
"""Build five paired courses from the verified 4A Unit 3 transcript (p23-30)."""
from __future__ import annotations

from pathlib import Path

from build_4a_starter_courses import (
    a, c, answer_text, child_listening, child_speaking, dialogue,
    json_write, parent_note, passage_statement, response, sentence,
    transcript_text, word,
)
from build_4a_unit2_courses import SECTION_SPECS, make_section, child_catalog_entry

ROOT = Path(__file__).resolve().parents[1]
BATCH = "4A-T1-W01"
DRAFT = ROOT / "content/drafts/4A-T1-W01-UNIT3"
DOCS = ROOT / "docs/course-batches"

META = {
    16: ("动物与家乡·基础识别", "p23-p24", "L1", "L1", 12, 12, "动物、家庭、家乡和动物卡字段", [2, 2, 2, 2, 3]),
    17: ("中国动物·歌谣信息", "p23-p25", "L1+", "L1", 14, 13, "三种动物、颜色、动作和家乡对应", [2, 2, 2, 2, 3]),
    18: ("云南大象·连续对话", "p23-p27", "L2", "L2", 17, 16, "多轮对话、人物动作、现在进行时", [2, 2, 2, 2, 3]),
    19: ("北极熊·阅读整合", "p23-p29", "L2+", "L2", 21, 18, "栖息地、食物、外形与因果", [1, 2, 2, 2, 3]),
    20: ("动物卡·Unit 3综合", "p23-p30", "L3", "L3", 25, 20, "跨动物信息整合与动物卡表达", [1, 1, 2, 2, 3]),
}


def tag(day, focus, micro=False):
    return (c if micro else a)(META[day][1], focus)


def w(day, heard, options, answer, focus, micro=False):
    return word(heard, options.split("|"), answer, tag(day, focus, micro))


def s(day, display, heard, same, focus):
    return sentence(display, heard, "same" if same else "different", tag(day, focus))


def r(day, prompt, options, answer, focus, micro=False):
    return response(prompt, options.split("|"), answer, tag(day, focus, micro))


def d(day, clips, question, options, answer, focus):
    return dialogue(clips, question, options.split("|"), answer, tag(day, focus))


def p(day, statement, correct, focus):
    return passage_statement(statement, correct, tag(day, focus))


def q(day, kind, prompt, expected="", hint="", focus="", micro=False):
    return kind, prompt, expected, hint, tag(day, focus, micro)


CONTENT = {
    16: {
        "words": [
            w(16, "panda", "panda|monkey|elephant", 0, "动物直接识别"),
            w(16, "elephant", "monkey|elephant|polar bear", 1, "动物直接识别"),
            w(16, "family", "hometown|family|animal", 1, "动物卡词汇"),
            w(16, "hometown", "hometown|home|family", 0, "听音选词相近词辨别", True),
        ],
        "sentences": [
            s(16, "This is a panda.", "This is a panda.", True, "动物身份"),
            s(16, "This is a polar bear.", "This is an elephant.", False, "相近动物辨别"),
            s(16, "An animal card tells us where animals live.", "An animal card tells us where animals live.", True, "动物卡字段"),
            s(16, "A baby elephant is in the elephant family.", "A baby elephant is in the elephant family.", True, "动物家庭"),
        ],
        "responses": [
            r(16, "What animal is this?", "It is a panda.|It is in China.|It is black and white.", 0, "动物身份问答"),
            r(16, "Where do the animals live?", "They eat fruit.|They live in China.|They are elephants.", 1, "问句选答语与字段辨别", True),
            r(16, "What can you put on an animal card?", "Where they live.|A school bag.|A classmate's name.", 0, "动物卡字段问答"),
            r(16, "Is this a baby elephant?", "Yes, it is.|Yes, they are.|It is a family.", 0, "动物身份回应"),
        ],
        "dialogues": [
            d(16, [["f", "Look at this panda."], ["m", "Let us make an animal card for it."]], "Which animal is on the card?", "A panda.|A monkey.|An elephant.", 0, "双句动物对应"),
            d(16, [["m", "This is an elephant."], ["f", "This is its baby."]], "Who is with the elephant?", "A panda.|A baby elephant.|A polar bear.", 1, "动物家庭对应"),
            d(16, [["f", "Where do they live?"], ["m", "We can write that on the card."]], "Which part of the card do they need?", "What they eat.|Where they live.|What they can do.", 1, "动物卡字段提取"),
            d(16, [["m", "I can see a monkey."], ["f", "I can see a panda too."]], "How many kinds of animals do they name?", "One.|Two.|Three.", 1, "两种动物信息"),
        ],
        "passage": "We are making an animal card. This card is about a panda. We write the animal's name and its hometown. We can also write what it eats, what it looks like, and what it can do.",
        "statements": [
            p(16, "The card is about a monkey.", False, "动物身份判断"),
            p(16, "The card has the animal's hometown.", True, "动物卡字段判断"),
            p(16, "The card can tell us what the animal eats.", True, "动物卡字段判断"),
            p(16, "The card is about a classmate.", False, "主题辨别"),
        ],
        "speaking": [
            q(16, "repeat", "This is a panda, and this is a monkey.", focus="双动物身份"),
            q(16, "repeat", "Here is an elephant family with a baby elephant.", focus="动物家庭"),
            q(16, "repeat", "This animal card is about a polar bear.", focus="卡片主题"),
            q(16, "repeat", "On an animal card, we write where they live.", focus="卡片栖息地字段"),
            q(16, "repeat", "We also write what they eat and what they can do.", focus="卡片多字段"),
            q(16, "repeat", "Let us make an animal card together.", focus="项目任务"),
            q(16, "qa", "What animal is this?", "It is a panda.", "用完整句回答：它是大熊猫。", "动物身份自主问答", True),
            q(16, "qa", "What can we make?", "We can make an animal card.", "用完整句回答：我们能制作动物卡。", "项目任务输出"),
        ],
    },
    17: {
        "words": [
            w(17, "Sichuan", "Sichuan|Guizhou|Yunnan", 0, "熊猫家乡识别"),
            w(17, "Guizhou", "Yunnan|Guizhou|Sichuan", 1, "猴子家乡识别"),
            w(17, "trunk", "tail|trunk|tree", 1, "大象动作词识别"),
            w(17, "light grey", "light grey|black and white|yellow and brown", 0, "听音选词与颜色辨别", True),
        ],
        "sentences": [
            s(17, "Pandas are black and white.", "Pandas are black and white.", True, "熊猫颜色"),
            s(17, "Monkeys are from Yunnan.", "Monkeys are from Guizhou.", False, "猴子家乡辨别"),
            s(17, "Elephants shower with their trunks.", "Elephants shower with their trunks.", True, "大象动作"),
            s(17, "Pandas jump in trees.", "Monkeys jump in trees.", False, "动物动作对应"),
        ],
        "responses": [
            r(17, "Where are pandas from?", "Sichuan.|Guizhou.|Yunnan.", 0, "熊猫家乡问答"),
            r(17, "Where are monkeys from?", "Yunnan.|Guizhou.|Sichuan.", 1, "问句选答语与家乡对应", True),
            r(17, "What colour are elephants in the chant?", "Black and white.|Yellow and brown.|Light grey.", 2, "大象颜色问答"),
            r(17, "What do monkeys do?", "They jump in trees.|They roll like a ball.|They shower with their trunks.", 0, "动物动作问答"),
        ],
        "dialogues": [
            d(17, [["f", "The pandas roll like a ball."], ["m", "Sichuan is their hometown."]], "Where are the pandas from?", "Sichuan.|Guizhou.|Yunnan.", 0, "动作与家乡双线索"),
            d(17, [["m", "These animals are yellow and brown."], ["f", "They jump in trees."]], "Which animals are they?", "Pandas.|Monkeys.|Elephants.", 1, "颜色动作整合"),
            d(17, [["f", "The elephants are light grey."], ["m", "They are from Yunnan."]], "Which place is their hometown?", "Sichuan.|Guizhou.|Yunnan.", 2, "大象家乡提取"),
            d(17, [["m", "Pandas are from Sichuan."], ["f", "Monkeys are from Guizhou."]], "Which animals are from Guizhou?", "Pandas.|Monkeys.|Elephants.", 1, "相邻动物家乡对应"),
        ],
        "passage": "In our chant, pandas are black and white and come from Sichuan. Monkeys are yellow and brown and come from Guizhou. Elephants are light grey and come from Yunnan. The monkeys jump in trees, and the elephants shower with their trunks.",
        "statements": [
            p(17, "Pandas are from Sichuan.", True, "熊猫家乡"),
            p(17, "Monkeys are light grey.", False, "动物颜色辨别"),
            p(17, "Elephants are from Yunnan.", True, "大象家乡"),
            p(17, "Pandas shower with their trunks.", False, "动物动作辨别"),
        ],
        "speaking": [
            q(17, "repeat", "Pandas are black and white, and they roll like a ball.", focus="熊猫颜色动作"),
            q(17, "repeat", "They are from Sichuan, and Sichuan is their hometown.", focus="熊猫家乡"),
            q(17, "repeat", "Monkeys are yellow and brown, and they jump in trees.", focus="猴子颜色动作"),
            q(17, "repeat", "They are from Guizhou, and Guizhou is their hometown.", focus="猴子家乡"),
            q(17, "repeat", "Elephants are light grey and shower with their trunks.", focus="大象颜色动作"),
            q(17, "repeat", "They are from Yunnan, and Yunnan is their hometown.", focus="大象家乡"),
            q(17, "qa", "Where are elephants from?", "They are from Yunnan.", "用完整句回答：它们来自云南。", "动物家乡自主问答", True),
            q(17, "qa", "What colour are monkeys?", "They are yellow and brown.", "用完整句回答：它们是黄色和棕色的。", "动物颜色输出"),
        ],
    },
    18: {
        "words": [
            w(18, "baby elephant", "baby elephant|elephant family|polar bear", 0, "小象识别"),
            w(18, "India and Africa", "Yunnan and Sichuan|India and Africa|Guizhou and Yunnan", 1, "其他栖息地识别"),
            w(18, "swimming", "playing|swimming|pulling", 1, "进行时动作识别"),
            w(18, "pulling by the tail", "pulling by the tail|playing in the river|giving bananas", 0, "听音选词与相近动作辨别", True),
        ],
        "sentences": [
            s(18, "The elephant family are playing in the river.", "The elephant family are playing in the river.", True, "象群动作"),
            s(18, "The baby elephant is playing in the trees.", "The baby elephant is swimming in the river.", False, "小象动作地点辨别"),
            s(18, "The mother elephant is pulling her baby by the tail.", "The mother elephant is pulling her baby by the tail.", True, "母象动作"),
            s(18, "The farmer is giving the elephants some apples.", "The farmer is giving the elephants some bananas.", False, "农民提供食物辨别"),
        ],
        "responses": [
            r(18, "Where are the elephants on TV from?", "Yunnan.|India.|Africa.", 0, "电视象群来源"),
            r(18, "What is the baby elephant doing?", "It is playing in the trees.|It is swimming in the river.|It is giving bananas.", 1, "问句选答语与动作对应", True),
            r(18, "Why do elephants like those places?", "There are trees and water nearby.|There is ice and snow.|There are no rivers.", 0, "栖息地原因"),
            r(18, "What is the farmer giving the elephants?", "Fish.|Leaves.|Bananas.", 2, "食物信息"),
        ],
        "dialogues": [
            d(18, [["f", "Look, the elephant family are playing in the river."], ["m", "They are from Yunnan."]], "Where are the elephants from?", "Yunnan.|India.|Africa.", 0, "多句来源提取"),
            d(18, [["m", "Can we see elephants in other places?"], ["f", "Yes, in India and Africa too."]], "Which other places are named?", "Sichuan and Guizhou.|India and Africa.|Yunnan and Guizhou.", 1, "地点双信息"),
            d(18, [["f", "The baby elephant is swimming."], ["m", "Its mother is pulling it back by the tail."]], "Who is pulling the baby back?", "The farmer.|The mother elephant.|Shenshen.", 1, "动作人物对应"),
            d(18, [["m", "The farmer is giving the elephants bananas."], ["f", "Yes, farmers are very kind to them."]], "Why are the farmers kind?", "They give bananas.|They pull the baby.|They swim in the river.", 0, "行为与评价整合"),
        ],
        "passage": "Shenshen and her mum are watching TV. An elephant family from Yunnan are playing in the river. A baby elephant is swimming. Its mother is pulling it back by the tail. A farmer is giving the elephants some bananas. Elephants like places with trees and water nearby.",
        "statements": [
            p(18, "Shenshen and her mum are watching TV.", True, "人物场景"),
            p(18, "The elephants are from India.", False, "象群来源"),
            p(18, "The mother elephant pulls her baby by the tail.", True, "母象动作"),
            p(18, "The farmer is giving fish to the elephants.", False, "食物辨别"),
        ],
        "speaking": [
            q(18, "repeat", "The elephant family are playing in the river.", focus="象群进行时"),
            q(18, "repeat", "They are from Yunnan.", focus="象群来源"),
            q(18, "repeat", "Elephants like places with trees and water nearby.", focus="栖息地"),
            q(18, "repeat", "The baby elephant is swimming in the river.", focus="小象进行时"),
            q(18, "repeat", "The mother elephant is pulling her baby by the tail.", focus="母象进行时"),
            q(18, "repeat", "The farmer is giving the elephants some bananas.", focus="农民进行时"),
            q(18, "qa", "What is the baby elephant doing?", "It is swimming in the river.", "用完整句回答：它正在河里游泳。", "动作与人物自主对应", True),
            q(18, "qa", "Where can we see elephants besides Yunnan?", "We can see them in India and Africa too.", "用完整句回答：我们也能在印度和非洲看到它们。", "多地点信息输出"),
        ],
    },
    19: {
        "words": [
            w(19, "the North Pole", "the North Pole|Yunnan|Guizhou", 0, "北极熊栖息地"),
            w(19, "thick fur", "white snow|thick fur|cold water", 1, "保暖外形"),
            w(19, "seals and fish", "fruit and leaves|bananas and leaves|seals and fish", 2, "北极熊食物"),
            w(19, "ice and snow", "ice and snow|trees and water|fruit and leaves", 0, "环境词组"),
            w(19, "swimming in cold water", "sleeping in snow|swimming in cold water|playing in trees", 1, "听音选词与动作环境辨别", True),
        ],
        "sentences": [
            s(19, "Polar bears live near the North Pole.", "Polar bears live near the North Pole.", True, "栖息地"),
            s(19, "Polar bears have thin fur to keep warm.", "Polar bears have thick fur to keep warm.", False, "外形细节"),
            s(19, "Polar bears catch seals and fish for food.", "Polar bears catch seals and fish for food.", True, "食物信息"),
            s(19, "Polar bears sleep in a bed of green leaves.", "Polar bears sleep in a bed of white snow.", False, "睡眠环境辨别"),
            s(19, "The ice and snow are melting as the weather gets warmer.", "The ice and snow are melting as the weather gets warmer.", True, "环境因果"),
        ],
        "responses": [
            r(19, "Where do polar bears live?", "Near the North Pole.|In Yunnan.|In Guizhou.", 0, "栖息地问答"),
            r(19, "What do polar bears eat?", "Fruit and leaves.|Seals and fish.|Bananas.", 1, "问句选答语与食物辨别", True),
            r(19, "Why do polar bears have thick fur?", "To keep warm.|To climb trees.|To catch bananas.", 0, "外形原因"),
            r(19, "Where do polar bears sleep?", "In the river.|In trees.|In white snow.", 2, "睡眠地点"),
            r(19, "What is happening to the ice and snow?", "They are growing.|They are melting.|They are swimming.", 1, "环境变化"),
        ],
        "dialogues": [
            d(19, [["f", "Polar bears live near the North Pole."], ["m", "It is very cold there, so they have thick fur."]], "Why do they have thick fur?", "To keep warm.|To swim faster.|To climb trees.", 0, "栖息地与外形因果"),
            d(19, [["m", "What do polar bears eat?"], ["f", "They catch seals and fish for food."]], "Which food is named?", "Bananas.|Seals and fish.|Fruit and leaves.", 1, "食物提取"),
            d(19, [["f", "There is lots of ice and snow."], ["m", "That is why polar bears look white."]], "Why do they look white?", "Because of ice and snow.|Because they eat fish.|Because they swim.", 0, "外形原因"),
            d(19, [["m", "Where do they sleep?"], ["f", "In a bed of white snow."], ["m", "And they swim in cold water too."]], "Which two places are named?", "Snow and cold water.|Trees and river.|Guizhou and Yunnan.", 0, "两种环境整合"),
            d(19, [["f", "The weather is getting warmer."], ["m", "The ice and snow are melting."], ["f", "Their lives can be very difficult."]], "What makes their lives difficult?", "Melting ice and snow.|Too many bananas.|A long tail.", 0, "跨句因果整合"),
        ],
        "passage": "Polar bears live near the North Pole, where it is very cold. Their thick fur helps them keep warm. They look white in the ice and snow. They swim in cold water and catch seals and fish for food. They sleep in white snow. When the weather gets warmer, the ice and snow melt, and life can be difficult for them.",
        "statements": [
            p(19, "Polar bears live near the North Pole.", True, "栖息地"),
            p(19, "Their fur is thin.", False, "外形辨别"),
            p(19, "They eat seals and fish.", True, "食物信息"),
            p(19, "They sleep in trees.", False, "睡眠地点"),
            p(19, "Melting ice and snow can make their lives difficult.", True, "环境因果"),
        ],
        "speaking": [
            q(19, "repeat", "Polar bears live near the North Pole.", focus="栖息地"),
            q(19, "repeat", "It is very cold there.", focus="环境"),
            q(19, "repeat", "They have thick fur to keep warm.", focus="外形原因"),
            q(19, "repeat", "They catch seals and fish for food.", focus="食物"),
            q(19, "repeat", "Polar bears sleep in a bed of white snow.", focus="睡眠环境"),
            q(19, "repeat", "The ice and snow are melting as the weather gets warmer.", focus="环境变化"),
            q(19, "qa", "What do polar bears eat?", "They eat seals and fish.", "用完整句回答：它们吃海豹和鱼。", "食物自主问答", True),
            q(19, "qa", "Why do polar bears have thick fur?", "They have thick fur to keep warm.", "用完整句回答：它们有厚皮毛来保暖。", "外形因果输出"),
        ],
    },
    20: {
        "words": [
            w(20, "fruit and leaves", "seals and fish|fruit and leaves|bananas and fish", 1, "猴子卡食物"),
            w(20, "swing on branches", "swim in water|swing on branches|roll like a ball", 1, "猴子能力"),
            w(20, "a long tail and long arms", "thick fur|a long tail and long arms|a light grey trunk", 1, "猴子外形"),
            w(20, "the North Pole", "Guizhou|the North Pole|Yunnan", 1, "北极熊家乡"),
            w(20, "giving the elephants bananas", "catching seals and fish|giving the elephants bananas|swinging on branches", 1, "听音选词与跨动物动作辨别", True),
        ],
        "sentences": [
            s(20, "The monkeys on the card are from Guizhou.", "The monkeys on the card are from Guizhou.", True, "动物卡来源"),
            s(20, "The monkeys eat seals and fish.", "The monkeys eat fruit and leaves.", False, "跨动物食物辨别"),
            s(20, "The monkeys have long tails and long arms.", "The monkeys have long tails and long arms.", True, "动物卡外形"),
            s(20, "The polar bears live in Yunnan.", "The polar bears live near the North Pole.", False, "跨动物栖息地"),
            s(20, "The baby elephant is swimming in the river.", "The baby elephant is swimming in the river.", True, "进行时综合"),
        ],
        "responses": [
            r(20, "What can the monkeys on the card do?", "They can swing on branches.|They can catch seals.|They can shower with trunks.", 0, "动物卡能力"),
            r(20, "What do polar bears eat?", "Fruit and leaves.|Seals and fish.|Bananas.", 1, "问句选答语与跨动物食物辨别", True),
            r(20, "Where are the elephants in the chant from?", "Sichuan.|Guizhou.|Yunnan.", 2, "大象家乡"),
            r(20, "What is the baby elephant doing?", "It is swimming.|It is climbing.|It is catching fish.", 0, "进行时动作"),
            r(20, "Where do elephants like living?", "In places with trees and water nearby.|In white snow.|On branches.", 0, "栖息地归纳"),
        ],
        "dialogues": [
            d(20, [["f", "This card is about monkeys from Guizhou."], ["m", "They eat fruit and leaves."], ["f", "They can swing on branches."]], "Which animal is on the card?", "Monkeys.|Polar bears.|Elephants.", 0, "动物卡多字段整合"),
            d(20, [["m", "Pandas come from Sichuan."], ["f", "Monkeys come from Guizhou."], ["m", "Elephants come from Yunnan."]], "Which animal is from Yunnan?", "Pandas.|Monkeys.|Elephants.", 2, "三动物家乡对应"),
            d(20, [["f", "The baby elephant is swimming."], ["m", "Its mother is pulling it back by the tail."], ["f", "A farmer is giving them bananas."]], "Who gives bananas?", "The baby.|The mother.|A farmer.", 2, "多人物动作对应"),
            d(20, [["m", "Polar bears have thick fur."], ["f", "They live near the North Pole and catch fish."], ["m", "They sleep in white snow."]], "Where do they sleep?", "In trees.|In white snow.|In a river.", 1, "北极熊多字段整合"),
            d(20, [["f", "Which card has long arms and a long tail?"], ["m", "The monkey card."], ["f", "And which card has thick fur?"], ["m", "The polar bear card."]], "Which card has thick fur?", "The monkey card.|The elephant card.|The polar bear card.", 2, "双卡对比"),
        ],
        "passage": "Here are three animal cards. The monkey card says monkeys live in Guizhou, eat fruit and leaves, and swing on branches. The elephant card says an elephant family from Yunnan are playing in a river. A farmer is giving them bananas. The polar bear card says polar bears live near the North Pole, have thick fur, and catch seals and fish. Ice and snow are melting there.",
        "statements": [
            p(20, "The monkey card says monkeys live in Guizhou.", True, "猴子来源"),
            p(20, "The monkeys eat seals and fish.", False, "跨动物食物辨别"),
            p(20, "The elephant family are playing in a river.", True, "大象动作"),
            p(20, "The polar bears have long tails.", False, "跨动物外形辨别"),
            p(20, "Ice and snow are melting near the polar bears.", True, "环境变化"),
        ],
        "speaking": [
            q(20, "repeat", "These monkeys are from Guizhou.", focus="动物卡来源"),
            q(20, "repeat", "They eat fruit and leaves.", focus="动物卡食物"),
            q(20, "repeat", "They have long tails and long arms.", focus="动物卡外形"),
            q(20, "repeat", "They can climb trees and swing on branches.", focus="动物卡能力"),
            q(20, "repeat", "The elephant family are playing in the river.", focus="进行时稳定输出"),
            q(20, "repeat", "Polar bears have thick fur to keep warm.", focus="外形因果稳定输出"),
            q(20, "qa", "Where do the monkeys on the card live?", "They live in Guizhou.", "用完整句回答：卡片上的猴子住在贵州。", "动物卡地点自主问答", True),
            q(20, "qa", "What can the monkeys on the card do?", "They can climb trees and swing on branches.", "用完整句回答：它们能爬树并在树枝上摆荡。", "动物卡能力整合输出"),
        ],
    },
}


# Extra guided QA increases actual oral output without introducing a new scoring type.
# The front-end and cloud function currently enforce exactly 8 questions; 02 owns that
# compatibility change. These are content candidates until its regression is complete.
SPEAKING_EXTRA = {
    16: [
        q(16, "qa", "What can we write on an animal card?", "We can write where animals live and what they eat.", "用完整句说出动物卡的居住地和食物两个栏目。", "动物卡双字段组织"),
        q(16, "qa", "Which animal is in the elephant family?", "The baby elephant is in the elephant family.", "用完整句回答：小象是大象家庭的一员。", "动物家庭信息对应"),
    ],
    17: [
        q(17, "qa", "Where are pandas from?", "They are from Sichuan.", "用完整句回答：熊猫来自四川。", "家乡信息对应"),
        q(17, "qa", "Which animals jump in trees?", "Monkeys jump in trees.", "用完整句回答：猴子在树上跳。", "动物动作对应"),
    ],
    18: [
        q(18, "qa", "What are the elephant family doing?", "They are playing in the river.", "用完整句回答：象群正在河里玩。", "复数进行时"),
        q(18, "qa", "What is the mother elephant doing?", "She is pulling her baby back by the tail.", "用完整句回答：母象正拉着小象尾巴把它拉回来。", "母象动作对应"),
        q(18, "qa", "What is the farmer doing?", "He is giving the elephants some bananas.", "用完整句回答：农民正给大象香蕉。", "农民动作对应"),
        q(18, "qa", "Where do elephants like living?", "They like living in places with trees and water nearby.", "用完整句回答：大象喜欢住在附近有树和水的地方。", "栖息地完整表达"),
    ],
    19: [
        q(19, "qa", "Where do polar bears live?", "They live near the North Pole.", "用完整句回答：北极熊住在北极附近。", "栖息地提取"),
        q(19, "qa", "Why do polar bears look white?", "They look white because there is lots of ice and snow.", "用完整句回答：因为那里有很多冰雪，所以它们看起来是白色的。", "外形因果表达"),
        q(19, "qa", "Where do polar bears sleep?", "They sleep in a bed of white snow.", "用完整句回答：它们睡在白雪铺成的床上。", "睡眠地点"),
        q(19, "qa", "What is happening to the ice and snow?", "The ice and snow are melting.", "用完整句回答：冰雪正在融化。", "环境变化表达"),
    ],
    20: [
        q(20, "qa", "What do the monkeys on the card eat?", "They eat fruit and leaves.", "用完整句回答：卡片上的猴子吃水果和叶子。", "动物卡食物"),
        q(20, "qa", "What do the monkeys look like?", "They have long tails and long arms.", "用完整句回答：它们有长尾巴和长手臂。", "动物卡外形"),
        q(20, "qa", "Where are the elephants from and what are they doing?", "They are from Yunnan and are playing in the river.", "用完整句同时说明：大象来自云南，正在河里玩。", "跨卡地点与动作整合"),
        q(20, "qa", "Where do polar bears live and what do they eat?", "They live near the North Pole and eat seals and fish.", "用完整句同时说明：北极熊住在北极附近，吃海豹和鱼。", "跨卡栖息地与食物整合"),
    ],
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
    return {"course_id": course_id, "weekly_batch_id": BATCH, "study_pack": pair, "pair_id": pair,
            "publication_status": "formal", "title": f"四上·第{day}课｜Unit 3{title}（听力）",
            "week": 4, "day": day - 15, "course_type": "weekly_test" if day == 20 else "training",
            "est_minutes": minutes, "scope": f"4A Unit 3 {scope}", "difficulty": difficulty,
            "scoring": {"per_question": 100 // count, "total": 100},
            "test_audio": f"static/audio/listening/{course_id}/hello.mp3",
            "test_transcript": [["n", "Hello! Can you hear me? Let us begin."]], "sections": sections}


def build_speaking(day):
    title, scope, _, difficulty, _, minutes, _, _ = META[day]
    course_id = f"S4A-T1-W01-D{day:02d}"
    pair = f"4A-T1-W01-D{day:02d}"
    questions = []
    for index, (kind, prompt, expected, hint, tag_value) in enumerate(CONTENT[day]["speaking"] + SPEAKING_EXTRA[day], 1):
        question = {"id": index, "type": kind, "audio": f"static/audio/speaking/{course_id}/q{index:02d}.mp3",
                    "tag": tag_value, "parent_note": parent_note(tag_value)}
        if kind == "repeat":
            question["text"] = prompt
        else:
            question.update({"question": prompt, "expected": expected, "hint": hint})
        questions.append(question)
    return {"course_id": course_id, "weekly_batch_id": BATCH, "study_pack": pair, "pair_id": pair,
            "publication_status": "formal", "title": f"四上·第{day}课｜Unit 3{title}（口语）",
            "week": 4, "day": day - 15, "course_type": "weekly_review" if day == 20 else "training",
            "est_minutes": minutes, "scope": f"4A Unit 3 {scope}", "difficulty": difficulty,
            "questions": questions}


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
    return {"weekly_batch_id": BATCH, "generation_status": "READY_TO_GENERATE",
            "publication_status": "formal", "expected_listening_outputs": listen_count,
            "expected_speaking_outputs": len(items) - listen_count, "expected_total_outputs": len(items), "items": items}


def documents(listening, speaking):
    mapping = ["# 4A 新教材 Unit 3 D16–D20 教材与课程映射", "",
               "> 内容开发交付稿；教材事实源为确认版教材 B005 逐页转录 p23–30。线上回归与部署由 02 窗口负责。", "",
               "| 课次 | 配对 ID | 教材范围 | 听力/口语 | 难度 | 时长 | 重点 |",
               "|---|---|---|---:|---|---:|---|"]
    parent = ["# 4A 新教材 Unit 3 D16–D20 家长版答案、原文与口语目标句", "",
              "> 家长专用，不作为儿童公开副本。线上回归与部署由 02 窗口负责。", ""]
    for day, lcourse, scourse in zip(range(16, 21), listening, speaking):
        title, scope, planned, _, lmins, smins, focus, _ = META[day]
        count = sum(len(section["questions"]) for section in lcourse["sections"])
        mapping.append(f"| D{day:02d}｜{title} | {lcourse['pair_id']} | Unit 3 {scope} | {count}+{len(scourse['questions'])} | {planned} | 约{lmins+smins}分钟 | {focus} |")
        parent += [f"## D{day:02d}｜{lcourse['course_id']} / {scourse['course_id']}", "",
                   f"教材：Unit 3 {scope}；难度：{planned}；听力 {count} 题，口语 6 repeat + {len(scourse['questions'])-6} QA。", "",
                   "### 听力答案与原文", ""]
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
    mapping += ["", "## 页段依据", "", "- D16 p23–24：单元任务、topic words 与动物卡字段。",
                "- D17 扩至 p25：熊猫、猴子、大象的颜色、动作和中国家乡。",
                "- D18 扩至 p27：云南象群、母象与农民动作、进行时规则。",
                "- D19 扩至 p29：北极熊栖息地、皮毛、食物和冰雪变化。",
                "- D20 扩至 p30：动物卡项目，综合本单元，不进入 p31 Unit 4。", "",
                "## A 主线与 C 微调", "", "- 共 166 题：A 主线 151、C 微调 15（约9%）。",
                "- 每课仅 2 道听力 C（听音选词、听问句选答语）和 1 道口语 C（QA）。",
                "- C 只沿用 00 先前给出的两类相对低正确率题型、人物/信息对应辨别摘要；本批全部仍用 Unit 3 页段材料，不推断新弱项。", "",
                "## 发布边界", "", "- 口语 10/10/12/12/12 题已获家长批准，但现有前端与云函数仍限制每课 8 题；02 兼容前不得部署。",
                "- 内容完成后设为 formal 可见候选；本窗口不推送、不部署、不生成学习记录。",
                "- 02 窗口负责扩展口语题量校验、完整回归、线上音频哈希和正式部署验收。", ""]
    return "\n".join(mapping), "\n".join(parent)


def main():
    listening = [build_listening(day) for day in range(16, 21)]
    speaking = [build_speaking(day) for day in range(16, 21)]
    for module, courses, child_builder in (("listening", listening, child_listening), ("speaking", speaking, child_speaking)):
        catalog = []
        for course in courses:
            json_write(ROOT / "content" / module / f"{course['course_id']}.json", course)
            child = child_builder(course)
            json_write(DRAFT / "child" / module / f"{course['course_id']}.json", child)
            catalog.append(child_catalog_entry(course, child))
        json_write(DRAFT / "child" / module / "catalog.json", catalog)
    packs = {"weekly_batch_id": BATCH, "publication_status": "formal", "visible": True,
             "authority_note": "父JSON为唯一活动源；本目录仅含配对、音频计划和派生儿童安全副本。02负责回归与线上部署。",
             "study_packs": [
                 {"lesson": day, "study_pack": listening[index]["study_pack"], "pair_id": listening[index]["pair_id"],
                  "planned_title": f"四上·第{day}课｜Unit 3{META[day][0]}", "textbook_scope": listening[index]["scope"],
                  "planned_difficulty": META[day][2], "json_difficulty": META[day][3],
                  "planned_total_minutes": META[day][4] + META[day][5], "focus": META[day][6],
                  "listening_course_id": listening[index]["course_id"], "speaking_course_id": speaking[index]["course_id"],
                  "publication_gate": "02完成回归测试及线上部署后验收；内容窗口不部署。"}
                 for index, day in enumerate(range(16, 21))]}
    json_write(DRAFT / "study-packs.json", packs)
    json_write(DRAFT / "audio-generation-plan.json", audio_plan(listening, speaking))
    mapping, parent = documents(listening, speaking)
    DOCS.mkdir(parents=True, exist_ok=True)
    (DOCS / "2026-09-17-4A-Unit3-D16-D20教材与课程映射.md").write_text(mapping, encoding="utf-8", newline="\n")
    (DOCS / "2026-09-17-4A-Unit3-D16-D20家长版答案原文.md").write_text(parent, encoding="utf-8", newline="\n")
    print("Built Unit 3 D16-D20: five listening, five speaking, five study packs.")


if __name__ == "__main__":
    main()
