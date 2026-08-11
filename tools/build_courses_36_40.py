# -*- coding: utf-8 -*-
"""Build the textbook-aligned M3U2 course batch W/S01D36-D40."""

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LISTENING_DIR = ROOT / "content" / "listening"
SPEAKING_DIR = ROOT / "content" / "speaking"
PARENT_DIR = ROOT.parent / "Week5"
OPEN_DATE = "2026-08-11"


def note(page, extra=""):
    return f"教材第{page}页" + (f"；{extra}" if extra else "")


def word(qid, heard, options, answer, tag, page):
    return {
        "id": qid,
        "type": "word_choice",
        "options": options,
        "answer": answer,
        "transcript": [["n", heard]],
        "audio": "",
        "tag": tag,
        "parent_note": note(page),
    }


def sentence(qid, display, heard, answer, tag, page, extra=""):
    return {
        "id": qid,
        "type": "sentence_judge",
        "display": display,
        "answer": answer,
        "transcript": [["n", heard]],
        "audio": "",
        "tag": tag,
        "parent_note": note(page, extra),
    }


def response(qid, prompt, options, answer, tag, page):
    return {
        "id": qid,
        "type": "question_response",
        "options": options,
        "answer": answer,
        "transcript": [["n", prompt]],
        "audio": "",
        "tag": tag,
        "parent_note": note(page),
    }


def dialogue(qid, clips, question, options, answer, tag, page):
    return {
        "id": qid,
        "type": "dialogue_choice",
        "question_text": question,
        "options": options,
        "answer": answer,
        "transcript": [list(clip) for clip in clips]
        + [["n", f"Question: {question}"]],
        "audio": "",
        "tag": tag,
        "parent_note": note(page),
    }


def passage_question(qid, statement, answer, tag, page, extra=""):
    return {
        "id": qid,
        "type": "passage_judge",
        "statement": statement,
        "answer": answer,
        "tag": tag,
        "parent_note": note(page, extra),
    }


def listening_course(day, title, scope, page, words, sentences, responses,
                     dialogues, passage_text, passage_questions):
    course_id = f"W01D{day:02d}"
    for question in words + sentences + responses + dialogues:
        question["audio"] = (
            f"static/audio/listening/{course_id}/q{question['id']:02d}.mp3"
        )
    return {
        "course_id": course_id,
        "title": title,
        "week": 5,
        "day": day - 35,
        "course_type": "weekly_test" if day == 40 else "training",
        "est_minutes": 20,
        "scope": scope,
        "difficulty": "L1",
        "open_date": OPEN_DATE,
        "scoring": {"per_question": 5, "total": 100},
        "test_audio": f"static/audio/listening/{course_id}/hello.mp3",
        "test_transcript": [["n", "Hello! Can you hear me? Let's begin."]],
        "sections": [
            {
                "id": "word_discrimination",
                "name": "听音选词",
                "tip": "听录音，选出你听到的单词",
                "max_plays": 2,
                "questions": words,
            },
            {
                "id": "sentence_meaning",
                "name": "听句判断",
                "tip": "听句子，判断和屏幕上句子的意思是不是一样",
                "max_plays": 2,
                "questions": sentences,
            },
            {
                "id": "question_response",
                "name": "听问句选答语",
                "tip": "听问题，选出合适的回答",
                "max_plays": 2,
                "questions": responses,
            },
            {
                "id": "dialogue",
                "name": "听对话选答案",
                "tip": "听对话和问题，选出正确答案",
                "max_plays": 2,
                "questions": dialogues,
            },
            {
                "id": "passage",
                "name": "听短文判断",
                "tip": "听短文，判断下面的句子对不对（√ 对 / × 错）",
                "max_plays": 3,
                "shared_audio": True,
                "passage_transcript": [["n", passage_text]],
                "passage_audio": f"static/audio/listening/{course_id}/p01.mp3",
                "questions": passage_questions,
            },
        ],
    }


def repeat(qid, text, page, tag="教材跟读"):
    return {
        "id": qid,
        "type": "repeat",
        "text": text,
        "audio": "",
        "tag": f"教材P{page}·{tag}",
        "parent_note": note(page),
    }


def qa(qid, question, expected, hint, page, tag="教材问答"):
    return {
        "id": qid,
        "type": "qa",
        "question": question,
        "expected": expected,
        "hint": hint,
        "audio": "",
        "tag": f"教材P{page}·{tag}",
        "parent_note": note(page),
    }


def speaking_course(day, title, questions):
    course_id = f"S01D{day:02d}"
    for question in questions:
        question["audio"] = (
            f"static/audio/speaking/{course_id}/q{question['id']:02d}.mp3"
        )
    return {
        "course_id": course_id,
        "title": title,
        "week": 5,
        "day": day - 35,
        "course_type": "weekly_review" if day == 40 else "training",
        "est_minutes": 10,
        "difficulty": "L1",
        "open_date": OPEN_DATE,
        "questions": questions,
    }


LISTENING = [
    listening_course(
        36,
        "听力训练 · M3U2 Around my home",
        "4A M3U2 教材第37页：家庭位置、街道、附近地点、Is/Are there问答 + 旧坑嵌入",
        37,
        [
            word(1, "street", ["street", "school", "shop"], 0, "M3U2·street", 37),
            word(2, "shops", ["ships", "shops", "shoes"], 1, "M3U2·shops", 37),
            word(3, "park", ["park", "post", "part"], 0, "M3U2·park", 37),
            word(4, "city", ["canteen", "city", "centre"], 1, "M3U2·city", 37),
        ],
        [
            sentence(5, "Jill's home is at No. 126, Garden Street.", "Jill's home is at No. 126, Garden Street.", "same", "M3U2·home address", 37),
            sentence(6, "There are many shops near my home.", "There are many shops near my home.", "same", "M3U2·near home", 37),
            sentence(7, "The park is in front of Jill's home.", "The park is behind Jill's home.", "different", "M3U2·behind", 37, "原文是behind"),
            sentence(8, "These are shops near the park.", "This is a shop near the park.", "different", "旧坑复现·this/these", 37, "原文是This is a shop"),
        ],
        [
            response(9, "Where is Jill's home?", ["It is at No. 126, Garden Street.", "It is a supermarket.", "There are many shops."], 0, "M3U2·Where is", 37),
            response(10, "Is there a park near Jill's home?", ["Yes, there is.", "Yes, it is.", "Yes, there are."], 0, "M3U2·Is there", 37),
            response(11, "Are there any shops near her home?", ["Yes, there are.", "Yes, there is.", "No, it isn't."], 0, "M3U2·Are there", 37),
            response(12, "Is this a supermarket?", ["Yes, it is.", "Yes, there is.", "Yes, they are."], 0, "旧坑复现·this question", 37),
        ],
        [
            dialogue(13, [("f", "Where is your home?"), ("f", "It is at No. 126, Garden Street.")], "Where is Jill's home?", ["On Garden Street.", "On Park Street.", "On Rainbow Road."], 0, "M3U2·home address", 37),
            dialogue(14, [("m", "Is there a park near your home?"), ("f", "Yes. It is behind my home.")], "Where is the park?", ["Behind her home.", "Next to the school.", "Between two shops."], 0, "M3U2·park position", 37),
            dialogue(15, [("f", "Is your home on Garden Street, Miss Fang?"), ("f", "No. It is on Park Street.")], "Where is Miss Fang's home?", ["On Star Road.", "On Park Street.", "On Garden Street."], 1, "M3U2·Park Street", 37),
            dialogue(16, [("m", "Are there any shops near Miss Fang's home?"), ("f", "Yes. There are some shops, a supermarket and some restaurants.")], "What is near her home?", ["Only a school.", "Shops and restaurants.", "Only a post office."], 1, "M3U2·nearby places", 37),
        ],
        "Jill's home is at No. 126, Garden Street. There are many shops near her home. There is a park too. It is behind her home. Miss Fang's home is on Park Street. There are some shops, a supermarket, some restaurants and a park near her home.",
        [
            passage_question(17, "Jill lives on Garden Street.", "true", "M3U2·Garden Street", 37),
            passage_question(18, "The park is in front of Jill's home.", "false", "M3U2·behind", 37, "原文是behind"),
            passage_question(19, "Miss Fang's home is on Park Street.", "true", "M3U2·Park Street", 37),
            passage_question(20, "There are no restaurants near Miss Fang's home.", "false", "M3U2·restaurants", 37, "原文说有restaurants"),
        ],
    ),
    listening_course(
        37,
        "听力训练 · M3U2 Places and positions",
        "4A M3U2 教材第38页：supermarket、post office、restaurant、next to、between + 旧坑嵌入",
        38,
        [
            word(1, "supermarket", ["supermarket", "restaurant", "post office"], 0, "M3U2·supermarket", 38),
            word(2, "post office", ["police office", "post office", "teachers' office"], 1, "M3U2·post office", 38),
            word(3, "restaurant", ["restaurant", "supermarket", "canteen"], 0, "M3U2·restaurant", 38),
            word(4, "between", ["behind", "between", "beside"], 1, "M3U2·between", 38),
        ],
        [
            sentence(5, "The supermarket is next to the post office.", "The supermarket is next to the post office.", "same", "M3U2·next to", 38),
            sentence(6, "The post office is between two shops.", "The post office is between two shops.", "same", "M3U2·between", 38),
            sentence(7, "The restaurant is behind the supermarket.", "The restaurant is next to the supermarket.", "different", "M3U2·position", 38, "原文是next to"),
            sentence(8, "There is an restaurant near my home.", "There is a restaurant near my home.", "different", "旧坑复现·a/an", 38, "原文是a restaurant"),
        ],
        [
            response(9, "What is this place?", ["It is a supermarket.", "It is between.", "There are shops."], 0, "M3U2·place name", 38),
            response(10, "Where is the post office?", ["It is a busy street.", "It is between the supermarket and the restaurant.", "There are many shops."], 1, "M3U2·between", 38),
            response(11, "Is there a restaurant near your home?", ["Yes, there is.", "Yes, it can.", "Yes, they are."], 0, "M3U2·Is there", 38),
            response(12, "Can you draw a map of the neighbourhood?", ["Yes, I can.", "Yes, there is.", "No, it isn't."], 0, "旧坑复现·can + base verb", 38),
        ],
        [
            dialogue(13, [("f", "Is there a supermarket near your home?"), ("m", "Yes. It is next to the park.")], "Where is the supermarket?", ["Next to the park.", "Behind the school.", "Between two restaurants."], 0, "M3U2·next to", 38),
            dialogue(14, [("m", "Where is the post office?"), ("f", "It is between the supermarket and the restaurant.")], "What is next to the post office?", ["A school and a park.", "A supermarket and a restaurant.", "A bakery and a hotel."], 1, "M3U2·between", 38),
            dialogue(15, [("f", "Are there any restaurants?"), ("m", "Yes. There are two near my home.")], "How many restaurants are there?", ["One.", "Two.", "Three."], 1, "M3U2·Are there", 38),
            dialogue(16, [("m", "What is between the two red shops?"), ("f", "The post office is between them.")], "What is between the shops?", ["A restaurant.", "A supermarket.", "A post office."], 2, "M3U2·between", 38),
        ],
        "There are many places near Ben's home. There is a supermarket next to the park. The post office is between the supermarket and a restaurant. There are two shops behind the restaurant. Ben draws a map and shows it to his classmates.",
        [
            passage_question(17, "There is a supermarket near Ben's home.", "true", "M3U2·supermarket", 38),
            passage_question(18, "The supermarket is behind the park.", "false", "M3U2·next to", 38, "原文是next to"),
            passage_question(19, "The post office is between two places.", "true", "M3U2·between", 38),
            passage_question(20, "Ben does not have a map.", "false", "M3U2·neighbourhood map", 38, "原文说Ben draws a map"),
        ],
    ),
    listening_course(
        38,
        "听力训练 · M3U2 At the street corner",
        "4A M3U2 教材第39页：问路、postcard、bakery、clothes shops、礼貌表达 + 旧坑嵌入",
        39,
        [
            word(1, "postcard", ["postcard", "post office", "picture"], 0, "M3U2·postcard", 39),
            word(2, "bakery", ["bakery", "library", "factory"], 0, "M3U2·bakery", 39),
            word(3, "clothes", ["clocks", "clothes", "clouds"], 1, "M3U2·clothes", 39),
            word(4, "pleasure", ["picture", "pleasure", "playground"], 1, "M3U2·pleasure", 39),
        ],
        [
            sentence(5, "The post office is behind the restaurant.", "The post office is behind the restaurant.", "same", "M3U2·post office", 39),
            sentence(6, "The bakery is next to the post office.", "The bakery is next to the post office.", "same", "M3U2·bakery", 39),
            sentence(7, "There are clothes shops on this street.", "There aren't any clothes shops on this street.", "different", "M3U2·clothes shops", 39, "原文是aren't any"),
            sentence(8, "There is a bakery next to the post office.", "There is a bakery next to the post office.", "same", "旧坑复现·a/an", 39),
        ],
        [
            response(9, "Excuse me. Is there a post office here?", ["Yes, there is.", "Yes, it is a postcard.", "No, they aren't."], 0, "M3U2·Excuse me", 39),
            response(10, "Where is the post office?", ["It is behind the restaurant.", "It is a postcard.", "There are some clothes."], 0, "M3U2·behind", 39),
            response(11, "Thank you so much, girls.", ["Let me see.", "It's our pleasure.", "Excuse me."], 1, "M3U2·polite response", 39),
            response(12, "Can Jill and Kitty show the lady the way?", ["Yes, they can.", "Yes, there is.", "No, she isn't."], 0, "旧坑复现·can + base verb", 39),
        ],
        [
            dialogue(13, [("f", "Excuse me. Is there a post office here?"), ("f", "Yes. It is behind the restaurant.")], "Where is the post office?", ["Behind the restaurant.", "Next to the bakery.", "Between two parks."], 0, "M3U2·asking the way", 39),
            dialogue(14, [("f", "Is there a bakery?"), ("f", "Yes. It is next to the post office.")], "What is next to the post office?", ["A hotel.", "A bakery.", "A school."], 1, "M3U2·bakery", 39),
            dialogue(15, [("f", "Are there any clothes shops on this street?"), ("f", "No, but there are some behind the park.")], "Where are the clothes shops?", ["Behind the park.", "On this street.", "Next to the restaurant."], 0, "M3U2·clothes shops", 39),
            dialogue(16, [("f", "We can show you the way."), ("f", "Thank you so much."), ("f", "It's our pleasure.")], "Who can show the way?", ["The lady.", "The girls.", "The postman."], 1, "M3U2·show the way", 39),
        ],
        "At the street corner, a lady asks Jill and Kitty for help. She wants to send a postcard. The post office is behind the restaurant. She also wants some bread. The bakery is next to the post office. The clothes shops are behind the park. The girls can show her the way. The lady thanks them, and they say, 'It's our pleasure.'",
        [
            passage_question(17, "The lady wants to send a postcard.", "true", "M3U2·postcard", 39),
            passage_question(18, "The post office is in front of the restaurant.", "false", "M3U2·behind", 39, "原文是behind"),
            passage_question(19, "The bakery is next to the post office.", "true", "M3U2·bakery", 39),
            passage_question(20, "The girls cannot show the lady the way.", "false", "M3U2·show the way", 39, "原文说can show"),
        ],
    ),
    listening_course(
        39,
        "听力训练 · M3U2 Nanjing Road",
        "4A M3U2 教材第40页：Nanjing Road阅读、centre、busy、shops、hotels、evening lights + 旧坑嵌入",
        40,
        [
            word(1, "centre", ["centre", "city", "street"], 0, "M3U2·centre", 40),
            word(2, "busy", ["busy", "bakery", "bright"], 0, "M3U2·busy", 40),
            word(3, "hotel", ["home", "hotel", "hall"], 1, "M3U2·hotel", 40),
            word(4, "lights", ["lights", "nights", "shops"], 0, "M3U2·lights", 40),
        ],
        [
            sentence(5, "Nanjing Road is in the centre of Shanghai.", "Nanjing Road is in the centre of Shanghai.", "same", "M3U2·Nanjing Road", 40),
            sentence(6, "Nanjing Road is very quiet.", "Nanjing Road is very busy.", "different", "M3U2·busy", 40, "原文是busy"),
            sentence(7, "The lights are bright and beautiful.", "The lights are bright and beautiful.", "same", "M3U2·evening lights", 40),
            sentence(8, "Nanjing Road has many shops.", "Nanjing Road has many shops.", "same", "旧坑复现·third-person has", 40),
        ],
        [
            response(9, "Where is Nanjing Road?", ["It is in the centre of Shanghai.", "It is behind a hotel.", "There are many shops."], 0, "M3U2·Where is", 40),
            response(10, "Is Nanjing Road busy?", ["Yes, it is.", "Yes, there are.", "No, it can't."], 0, "M3U2·Is question", 40),
            response(11, "Why do people visit Nanjing Road in the evening?", ["The lights are bright and beautiful.", "There are no shops.", "The road is near a school."], 0, "M3U2·evening", 40),
            response(12, "What can people buy there?", ["They can buy clothes and watches.", "The lights are bright.", "The hotels are busy."], 0, "旧坑复现·can + base verb", 40),
        ],
        [
            dialogue(13, [("m", "Where is Nanjing Road?"), ("f", "It is in the centre of Shanghai.")], "Where is Nanjing Road?", ["In the centre of Shanghai.", "Behind Shanghai.", "Next to a school."], 0, "M3U2·centre", 40),
            dialogue(14, [("f", "What can people buy there?"), ("m", "They can buy clothes, clocks, watches and food.")], "What can people buy?", ["Only postcards.", "Clothes and watches.", "Only bread."], 1, "M3U2·shops", 40),
            dialogue(15, [("m", "Can people eat on Nanjing Road?"), ("f", "Yes. They can eat in the restaurants.")], "Where can people eat?", ["In the hotels.", "In the restaurants.", "In the post office."], 1, "M3U2·restaurants", 40),
            dialogue(16, [("f", "Why is the road beautiful in the evening?"), ("m", "The lights are bright then.")], "What is bright?", ["The hotels.", "The shops.", "The lights."], 2, "M3U2·lights", 40),
        ],
        "Nanjing Road is in the centre of Shanghai. It is very busy. Every day many people visit the shops. They can buy clothes, clocks, watches, food and many other things. They can eat in the restaurants or stay in the hotels. In the evening, many people visit the road because the lights are bright and beautiful.",
        [
            passage_question(17, "Nanjing Road is in Shanghai.", "true", "M3U2·Shanghai", 40),
            passage_question(18, "People can only buy food there.", "false", "M3U2·shops", 40, "原文还有clothes、clocks、watches等"),
            passage_question(19, "People can stay in the hotels.", "true", "M3U2·hotels", 40),
            passage_question(20, "The lights are dark in the evening.", "false", "M3U2·lights", 40, "原文是bright and beautiful"),
        ],
    ),
    listening_course(
        40,
        "听力周测卷 · M3U2 Around my home",
        "4A M3U2 教材第37-41页综合：地点、方位、问路、Nanjing Road、sl/sn/sw + 旧坑嵌入",
        41,
        [
            word(1, "slide", ["slide", "snake", "swing"], 0, "M3U2·sl sound", 41),
            word(2, "snake", ["swing", "street", "snake"], 2, "M3U2·sn sound", 41),
            word(3, "swing", ["slide", "swing", "shop"], 1, "M3U2·sw sound", 41),
            word(4, "street", ["street", "restaurant", "centre"], 0, "M3U2·unit word", 41),
        ],
        [
            sentence(5, "The home is next to the school.", "The home is next to the school.", "same", "M3U2·rhyme", 41),
            sentence(6, "The school is behind the trees.", "The school is in front of the trees.", "different", "M3U2·in front of", 41, "原文是in front of"),
            sentence(7, "The trees are behind the school.", "The trees are behind the school.", "same", "M3U2·behind", 41),
            sentence(8, "This is a swing.", "These are two swings.", "different", "旧坑复现·this/these", 41, "原文是These are"),
        ],
        [
            response(9, "Where is your home?", ["It is on Green Street.", "There are many shops.", "It is a supermarket."], 0, "M3U2·rhyme", 41),
            response(10, "Where is the school?", ["In front of the trees.", "Behind the home.", "Between two hotels."], 0, "M3U2·rhyme", 41),
            response(11, "Is there a post office near the restaurant?", ["Yes, there is.", "Yes, it does.", "Yes, they are."], 0, "M3U2·Is there review", 41),
            response(12, "What can people do on Nanjing Road?", ["They can visit the shops.", "There are many shops.", "The shops are busy."], 0, "旧坑复现·can + base verb", 41),
        ],
        [
            dialogue(13, [("f", "Excuse me. Where is the post office?"), ("m", "It is behind the restaurant.")], "Where is the post office?", ["Behind the restaurant.", "Next to the school.", "In front of the park."], 0, "M3U2·asking the way", 41),
            dialogue(14, [("m", "Is there a bakery?"), ("f", "Yes. It is next to the post office.")], "What is next to the post office?", ["A supermarket.", "A bakery.", "A hotel."], 1, "M3U2·next to review", 41),
            dialogue(15, [("f", "Where is the supermarket?"), ("m", "It is between the park and the restaurant.")], "What is between two places?", ["The supermarket.", "The school.", "The home."], 0, "M3U2·between review", 41),
            dialogue(16, [("m", "Why do people visit Nanjing Road in the evening?"), ("f", "The lights are bright and beautiful.")], "Why do people visit in the evening?", ["To see the lights.", "To go to school.", "To find a snake."], 0, "M3U2·Nanjing Road review", 41),
        ],
        "My home is on Green Street, next to the school. The school is in front of some trees. There is a supermarket near my home. The post office is between the supermarket and a restaurant. The bakery is next to the post office. On Nanjing Road, people can visit many shops. In the evening, the lights are bright and beautiful. In the park, there are swings and a slide.",
        [
            passage_question(17, "The home is next to the school.", "true", "M3U2·rhyme", 41),
            passage_question(18, "The post office is behind the supermarket.", "false", "M3U2·between", 41, "原文是between the supermarket and a restaurant"),
            passage_question(19, "People can visit shops on Nanjing Road.", "true", "M3U2·Nanjing Road", 41),
            passage_question(20, "There are no swings in the park.", "false", "M3U2·sw sound", 41, "原文说有swings"),
        ],
    ),
]


SPEAKING = [
    speaking_course(
        36,
        "口语练习 · M3U2 Around my home",
        [
            repeat(1, "Where is your home?", 37),
            repeat(2, "It's at No. 126, Garden Street.", 37),
            repeat(3, "There are many shops near my home.", 37),
            repeat(4, "Is there a park near your home?", 37),
            repeat(5, "Yes, there is.", 37),
            repeat(6, "It's behind my home.", 37),
            qa(7, "Where is Jill's home?", "It's at No. 126, Garden Street.", "用英语说：在花园街126号。", 37),
            qa(8, "Are there any shops near Jill's home?", "Yes, there are.", "用英语说：是的，有。", 37, "旧坑复现"),
        ],
    ),
    speaking_course(
        37,
        "口语练习 · M3U2 Places and positions",
        [
            repeat(1, "This is a supermarket.", 38, "旧坑复现"),
            repeat(2, "This is a post office.", 38),
            repeat(3, "This is a restaurant.", 38),
            repeat(4, "The post office is next to the restaurant.", 38),
            repeat(5, "The post office is between the supermarket and the restaurant.", 38),
            repeat(6, "There are many shops near my home.", 38),
            qa(7, "Is there a supermarket near your home?", "Yes, there is.", "用英语说：是的，有。", 38),
            qa(8, "Where is the post office?", "It is between the supermarket and the restaurant.", "用英语说：它在超市和餐馆中间。", 38),
        ],
    ),
    speaking_course(
        38,
        "口语练习 · M3U2 At the street corner",
        [
            repeat(1, "Excuse me.", 39),
            repeat(2, "Is there a post office here?", 39),
            repeat(3, "I want to send a postcard.", 39),
            repeat(4, "It's behind the restaurant.", 39),
            repeat(5, "There's a bakery next to the post office.", 39, "旧坑复现"),
            repeat(6, "We can show you the way.", 39),
            qa(7, "Is there a bakery?", "Yes, there is.", "用英语说：是的，有。", 39),
            qa(8, "What do Jill and Kitty say?", "It's our pleasure.", "用英语说：这是我们的荣幸。", 39),
        ],
    ),
    speaking_course(
        39,
        "口语练习 · M3U2 Nanjing Road",
        [
            repeat(1, "Nanjing Road is in the centre of Shanghai.", 40),
            repeat(2, "It is very busy.", 40),
            repeat(3, "Many people visit the shops.", 40),
            repeat(4, "They can buy clothes and watches.", 40, "旧坑复现"),
            repeat(5, "They can eat in the restaurants.", 40),
            repeat(6, "The lights are bright and beautiful.", 40),
            qa(7, "Where is Nanjing Road?", "It is in the centre of Shanghai.", "用英语说：它在上海市中心。", 40),
            qa(8, "What can people buy there?", "They can buy clothes and watches.", "用英语说：他们可以买衣服和手表。", 40),
        ],
    ),
    speaking_course(
        40,
        "口语周复习 · M3U2 Around my home",
        [
            repeat(1, "Where is your home?", 41),
            repeat(2, "It's on Green Street.", 41),
            repeat(3, "It's next to the school.", 41),
            repeat(4, "Where is the school?", 41),
            repeat(5, "It is in front of the trees.", 41),
            repeat(6, "Slide starts with sl, snake with sn, and swing with sw.", 41),
            qa(7, "Where are the trees?", "They are behind the school.", "用英语说：它们在学校后面。", 41),
            qa(8, "Is there a slide near the school?", "Yes, there is.", "用英语说：是的，有。", 41),
        ],
    ),
]


def write_json(course, directory):
    path = directory / f"{course['course_id']}.json"
    path.write_text(
        json.dumps(course, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def transcript_text(parts):
    return " / ".join(text for _, text in parts)


def listening_parent_doc(courses):
    lines = [
        "# W01D36-40 听力答案与原文（家长版）",
        "",
        "> 生成日期：2026-08-11  ",
        "> 对齐规则：W/S 同课同页；本批只覆盖已学完的 4A M3U2 第37-41页，不进入 M3U3。  ",
        "> 内容比例：约90% M3U2 + 约10% 已学旧坑复现。",
        "",
    ]
    section_titles = {
        "word_discrimination": "听音选词",
        "sentence_meaning": "听句判断",
        "question_response": "听问句选答语",
        "dialogue": "听对话选答案",
        "passage": "听短文判断",
    }
    for course in courses:
        lines.append(f"## {course['course_id']} · {course['title']}")
        lines.append("")
        for section in course["sections"]:
            lines.append(f"### {section_titles[section['id']]}")
            lines.append("")
            if section["id"] == "passage":
                lines.append(
                    f"- 短文原文：{transcript_text(section['passage_transcript'])}"
                )
            for question in section["questions"]:
                parent_note = question["parent_note"]
                if question["type"] == "word_choice":
                    answer = question["options"][question["answer"]]
                    lines.append(
                        f"- Q{question['id']:02d} 原文：{transcript_text(question['transcript'])}｜"
                        f"答案：{answer}｜{parent_note}"
                    )
                elif question["type"] == "sentence_judge":
                    answer = "相同" if question["answer"] == "same" else "不同"
                    lines.append(
                        f"- Q{question['id']:02d} 屏显：{question['display']}｜"
                        f"原文：{transcript_text(question['transcript'])}｜"
                        f"答案：{answer}｜{parent_note}"
                    )
                elif question["type"] == "question_response":
                    answer = question["options"][question["answer"]]
                    lines.append(
                        f"- Q{question['id']:02d} 原文：{transcript_text(question['transcript'])}｜"
                        f"答案：{answer}｜{parent_note}"
                    )
                elif question["type"] == "dialogue_choice":
                    answer = question["options"][question["answer"]]
                    lines.append(
                        f"- Q{question['id']:02d} 原文：{transcript_text(question['transcript'])}｜"
                        f"答案：{answer}｜{parent_note}"
                    )
                else:
                    answer = "正确" if question["answer"] == "true" else "错误"
                    lines.append(
                        f"- Q{question['id']:02d} 判断：{question['statement']}｜"
                        f"答案：{answer}｜{parent_note}"
                    )
            lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def speaking_parent_doc(courses):
    lines = [
        "# S01D36-40 口语课文与答案（家长版）",
        "",
        "> 生成日期：2026-08-11  ",
        "> 规则：每课8题，6题 repeat + 2题 qa；与同编号听力课程逐页对齐，不进入 M3U3。  ",
        "> 地址题只使用教材虚构地址，不要求孩子提供真实住址。",
        "",
    ]
    for course in courses:
        lines.append(f"## {course['course_id']} · {course['title']}")
        lines.append("")
        for question in course["questions"]:
            if question["type"] == "repeat":
                lines.append(
                    f"- Q{question['id']:02d} 跟读：{question['text']}｜"
                    f"{question['parent_note']}"
                )
            else:
                lines.append(
                    f"- Q{question['id']:02d} 问题：{question['question']}｜"
                    f"目标答案：{question['expected']}｜屏显提示：{question['hint']}｜"
                    f"{question['parent_note']}"
                )
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def main():
    LISTENING_DIR.mkdir(parents=True, exist_ok=True)
    SPEAKING_DIR.mkdir(parents=True, exist_ok=True)
    PARENT_DIR.mkdir(parents=True, exist_ok=True)
    for course in LISTENING:
        write_json(course, LISTENING_DIR)
    for course in SPEAKING:
        write_json(course, SPEAKING_DIR)
    (PARENT_DIR / "W01D36-40_听力答案与原文_家长版.md").write_text(
        listening_parent_doc(LISTENING), encoding="utf-8"
    )
    (PARENT_DIR / "S01D36-40_口语课文与答案_家长版.md").write_text(
        speaking_parent_doc(SPEAKING), encoding="utf-8"
    )
    print("Built 5 listening courses, 5 speaking courses, and 2 parent documents.")


if __name__ == "__main__":
    main()
