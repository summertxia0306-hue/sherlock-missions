# -*- coding: utf-8 -*-
"""Build the textbook-aligned M3U1 course batch W/S01D31-D35."""

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LISTENING_DIR = ROOT / "content" / "listening"
SPEAKING_DIR = ROOT / "content" / "speaking"
PARENT_DIR = ROOT.parent / "Week4"
OPEN_DATE = "2026-08-06"


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
    cid = f"W01D{day:02d}"
    for question in words + sentences + responses + dialogues:
        question["audio"] = f"static/audio/listening/{cid}/q{question['id']:02d}.mp3"
    return {
        "course_id": cid,
        "title": title,
        "week": 4,
        "day": day - 30,
        "course_type": "weekly_test" if day == 35 else "training",
        "est_minutes": 20,
        "scope": scope,
        "difficulty": "L1",
        "open_date": OPEN_DATE,
        "scoring": {"per_question": 5, "total": 100},
        "test_audio": f"static/audio/listening/{cid}/hello.mp3",
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
                "passage_audio": f"static/audio/listening/{cid}/p01.mp3",
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
    cid = f"S01D{day:02d}"
    for question in questions:
        question["audio"] = f"static/audio/speaking/{cid}/q{question['id']:02d}.mp3"
    return {
        "course_id": cid,
        "title": title,
        "week": 4,
        "day": day - 30,
        "course_type": "weekly_review" if day == 35 else "training",
        "est_minutes": 10,
        "difficulty": "L1",
        "open_date": OPEN_DATE,
        "questions": questions,
    }


LISTENING = [
    listening_course(
        31,
        "听力训练 · M3U1 School places",
        "4A M3U1 教材第32页：校园地点、behind/in front of + 已学句型轻复现",
        32,
        [
            word(1, "canteen", ["canteen", "classroom", "garden"], 0, "M3U1·canteen", 32),
            word(2, "computer lab", ["music room", "computer lab", "classroom"], 1, "M3U1·computer lab", 32),
            word(3, "office", ["library", "canteen", "office"], 2, "M3U1·office", 32),
            word(4, "gym", ["gym", "garden", "hall"], 0, "M3U1·gym", 32),
        ],
        [
            sentence(5, "The English classroom is very small.", "The English classroom is very small.", "same", "M3U1·school rhyme", 32),
            sentence(6, "The English teacher is very tall.", "The English teacher is very short.", "different", "M3U1·school rhyme", 32, "原文是short"),
            sentence(7, "The gym is behind the office.", "The gym is behind the office.", "same", "M3U1·behind", 32),
            sentence(8, "Her name is Amy.", "His name is Jimmy.", "different", "旧坑复现·his/her", 32, "原文是His name is Jimmy"),
        ],
        [
            response(9, "What is this?", ["It is a canteen.", "It is behind.", "It is tall."], 0, "M3U1·school place", 32),
            response(10, "Where is the gym?", ["It is a gym.", "It is behind the office.", "It is very tall."], 1, "M3U1·behind", 32),
            response(11, "Is this a computer lab?", ["Yes, it is.", "Yes, he is.", "Yes, I can."], 0, "旧坑复现·一般疑问句", 32),
            response(12, "What can Kim do?", ["Kim is a student.", "Kim can study with Amy.", "Kim has a book."], 1, "旧坑复现·can", 32),
        ],
        [
            dialogue(13, [("f", "Is this the canteen?"), ("m", "Yes, it is.")], "What place is it?", ["The office.", "The canteen.", "The gym."], 1, "M3U1·canteen", 32),
            dialogue(14, [("m", "Where is the gym?"), ("f", "It is behind the office.")], "Where is the gym?", ["Behind the office.", "In the office.", "In front of the lab."], 0, "M3U1·behind", 32),
            dialogue(15, [("f", "The computer lab is in front of the gym."), ("m", "I can see it now.")], "What is in front of the gym?", ["The canteen.", "The office.", "The computer lab."], 2, "M3U1·in front of", 32),
            dialogue(16, [("m", "Her name is Amy."), ("f", "She studies with Kim.")], "Who studies with Kim?", ["Amy.", "Jimmy.", "The teacher."], 0, "旧坑复现·her/she", 32),
        ],
        "Welcome to our school. There is a canteen, a computer lab, an office and a gym. The computer lab is in front of the gym. The gym is behind the office. Amy and Jimmy study with Kim. Their English classroom is small.",
        [
            passage_question(17, "There is a canteen in the school.", "true", "M3U1·canteen", 32),
            passage_question(18, "The computer lab is behind the gym.", "false", "M3U1·in front of", 32, "原文是in front of"),
            passage_question(19, "The gym is behind the office.", "true", "M3U1·behind", 32),
            passage_question(20, "The English classroom is very big.", "false", "M3U1·school rhyme", 32, "原文是small"),
        ],
    ),
    listening_course(
        32,
        "听力训练 · M3U1 In our school",
        "4A M3U1 教材第33页：There is/are、学校设施与用途 + likes轻复现",
        33,
        [
            word(1, "building", ["building", "bookshelf", "biscuit"], 0, "M3U1·building", 33),
            word(2, "busy", ["big", "busy", "behind"], 1, "M3U1·busy", 33),
            word(3, "library", ["laboratory", "playground", "library"], 2, "M3U1·library", 33),
            word(4, "playground", ["playground", "computer lab", "classroom"], 0, "M3U1·playground", 33),
        ],
        [
            sentence(5, "There is a library.", "There is a library.", "same", "M3U1·There is", 33),
            sentence(6, "There are some computers.", "There are some computers.", "same", "M3U1·There are", 33),
            sentence(7, "Miss Fang is busy.", "Miss Fang is happy.", "different", "M3U1·busy", 33, "原文是happy"),
            sentence(8, "She likes reading in the library.", "She likes reading in the library.", "same", "旧坑复现·likes + V-ing", 33),
        ],
        [
            response(9, "What is in the computer lab?", ["Some books.", "Some computers.", "Some flowers."], 1, "M3U1·computer lab", 33),
            response(10, "Where do the children have lunch?", ["In the canteen.", "In the gym.", "In the office."], 0, "M3U1·have lunch", 33),
            response(11, "Where is the playground?", ["Behind the classroom building.", "In the classroom building.", "On the computer."], 0, "M3U1·behind", 33),
            response(12, "Does Jill like reading?", ["Yes, she does.", "Yes, she is.", "Yes, she can."], 0, "旧坑复现·does", 33),
        ],
        [
            dialogue(13, [("f", "This is our classroom building."), ("m", "It is big.")], "What are they looking at?", ["A garden.", "A classroom building.", "A playground."], 1, "M3U1·building", 33),
            dialogue(14, [("m", "There is a teachers' office."), ("f", "Miss Fang is busy there.")], "Who is busy?", ["Miss Fang.", "Peter.", "Mr Black."], 0, "M3U1·office", 33),
            dialogue(15, [("f", "There are a lot of books in the library."), ("m", "I like reading there.")], "What is in the library?", ["A lot of books.", "Some computers.", "A swing."], 0, "M3U1·library", 33),
            dialogue(16, [("m", "Can the children run in the playground?"), ("f", "Yes, they can run and play there.")], "What can the children do there?", ["Have lunch.", "Run and play.", "Read books."], 1, "旧坑复现·can + base verb", 33),
        ],
        "Welcome to Rainbow Primary School. There is a classroom building. There is a teachers' office, and Miss Fang is busy there. There are some computers in the computer lab and a lot of books in the library. The children have lunch in the canteen. The playground is behind the classroom building.",
        [
            passage_question(17, "There is a classroom building.", "true", "M3U1·There is", 33),
            passage_question(18, "There are some books in the computer lab.", "false", "M3U1·computer lab", 33, "原文是computers"),
            passage_question(19, "The children have lunch in the canteen.", "true", "M3U1·canteen", 33),
            passage_question(20, "The playground is in front of the classroom building.", "false", "M3U1·behind", 33, "原文是behind"),
        ],
    ),
    listening_course(
        33,
        "听力训练 · A visit to Rainbow Primary School",
        "4A M3U1 教材第34页：参观学校、楼层、花园、clean and tidy + 礼貌表达复现",
        34,
        [
            word(1, "floor", ["flower", "floor", "forest"], 1, "M3U1·floor", 34),
            word(2, "garden", ["garden", "canteen", "building"], 0, "M3U1·garden", 34),
            word(3, "cupboard", ["computer", "cupboard", "classroom"], 1, "M3U1·cupboard", 34),
            word(4, "tidy", ["thirsty", "tired", "tidy"], 2, "M3U1·tidy", 34),
        ],
        [
            sentence(5, "The garden is in front of the classroom building.", "The garden is in front of the classroom building.", "same", "M3U1·garden position", 34),
            sentence(6, "There is a swing and a slide.", "There is a swing and a slide.", "same", "M3U1·garden", 34),
            sentence(7, "The computer lab is on this floor.", "The library is on this floor.", "different", "M3U1·floor", 34, "原文是library"),
            sentence(8, "The classroom is clean and tidy.", "The classroom is clean and tidy.", "same", "M3U1·clean and tidy", 34),
        ],
        [
            response(9, "What's on this floor?", ["There is a computer lab.", "It is a clean floor.", "The floor is behind us."], 0, "M3U1·floor", 34),
            response(10, "What's in the garden?", ["Some computers.", "Some flowers and plants.", "Some desks and chairs."], 1, "M3U1·garden", 34),
            response(11, "How is the classroom?", ["It is clean and tidy.", "It is hungry and thirsty.", "It is ten years old."], 0, "M3U1·clean and tidy", 34),
            response(12, "Thank you for showing me around.", ["I'm sorry.", "You're welcome.", "Have some water."], 1, "旧坑复现·礼貌回应", 34),
        ],
        [
            dialogue(13, [("f", "Welcome to Rainbow Primary School."), ("m", "Thank you. Please show me around.")], "What does the man want to do?", ["Have lunch.", "See the school.", "Read a story."], 1, "M3U1·show around", 34),
            dialogue(14, [("m", "What's on this floor?"), ("f", "There is a computer lab. We have computer lessons there.")], "What is on this floor?", ["A computer lab.", "A canteen.", "A gym."], 0, "M3U1·floor", 34),
            dialogue(15, [("f", "This is our classroom."), ("m", "The cupboard and the bookshelf are tidy.")], "What two things are tidy?", ["The desks and chairs.", "The swing and slide.", "The cupboard and bookshelf."], 2, "M3U1·classroom", 34),
            dialogue(16, [("m", "Is that your classroom?"), ("f", "Yes, it is. It is clean and tidy.")], "Is the classroom tidy?", ["Yes, it is.", "No, it isn't.", "Yes, she is."], 0, "旧坑复现·一般疑问句", 34),
        ],
        "Mr Black is visiting Rainbow Primary School. Peter and Alice show him around. There is a garden in front of the classroom building. There are flowers, plants, a swing and a slide in the garden. The computer lab is on this floor. Their classroom has a cupboard and a bookshelf. It is clean and tidy. Mr Black says thank you, and the children say, 'You're welcome.'",
        [
            passage_question(17, "Mr Black visits Rainbow Primary School.", "true", "M3U1·school visit", 34),
            passage_question(18, "The garden is behind the classroom building.", "false", "M3U1·in front of", 34, "原文是in front of"),
            passage_question(19, "There is a computer lab on this floor.", "true", "M3U1·floor", 34),
            passage_question(20, "The classroom is not tidy.", "false", "M3U1·clean and tidy", 34, "原文是clean and tidy"),
        ],
    ),
    listening_course(
        34,
        "听力训练 · Animal School",
        "4A M3U1 教材第35页：Animal School、情绪、能力与鼓励 + can旧坑复现",
        35,
        [
            word(1, "forest", ["forest", "floor", "fruit"], 0, "M3U1·forest", 35),
            word(2, "river", ["rabbit", "river", "ruler"], 1, "M3U1·river", 35),
            word(3, "rabbit", ["rabbit", "river", "rubber"], 0, "M3U1·rabbit", 35),
            word(4, "try", ["tree", "tidy", "try"], 2, "M3U1·try", 35),
        ],
        [
            sentence(5, "There are no classrooms in Animal School.", "There are no classrooms in Animal School.", "same", "M3U1·Animal School", 35),
            sentence(6, "Little Rabbit can swim.", "Little Rabbit can't swim.", "different", "M3U1·can't", 35, "原文是can't"),
            sentence(7, "Little Rabbit can run fast.", "Little Rabbit can run fast.", "same", "M3U1·can run", 35),
            sentence(8, "The mouse can bite the net.", "The mouse can bite the net.", "same", "旧坑复现·can + base verb", 35),
        ],
        [
            response(9, "What's the matter?", ["I'm sad.", "I'm a rabbit.", "I'm in the forest."], 0, "M3U1·daily expression", 35),
            response(10, "Can Little Rabbit swim?", ["Yes, it is.", "No, it can't.", "No, it doesn't."], 1, "M3U1·can question", 35),
            response(11, "What can Little Rabbit do?", ["It can run fast.", "It is in the river.", "It has a classroom."], 0, "M3U1·run fast", 35),
            response(12, "Little Rabbit is afraid to try. What can you say?", ["Have a try!", "I'm full.", "You're ten."], 0, "M3U1·Have a try", 35),
        ],
        [
            dialogue(13, [("f", "What's the matter, Little Rabbit?"), ("m", "I can't swim. I'm sad.")], "How does Little Rabbit feel?", ["Happy.", "Sad.", "Hungry."], 1, "M3U1·feelings", 35),
            dialogue(14, [("m", "I'm a bad student."), ("f", "I don't think so. Come on! Have a try!")], "What does the teacher say?", ["Have a try!", "Have some biscuits.", "Go to the canteen."], 0, "M3U1·encouragement", 35),
            dialogue(15, [("f", "Can you climb trees?"), ("m", "No, I can't. But I can run fast.")], "What can the rabbit do?", ["Swim.", "Climb trees.", "Run fast."], 2, "M3U1·ability", 35),
            dialogue(16, [("m", "The rabbit runs very fast."), ("f", "Yes. It is first today.")], "Who is first?", ["Mr Owl.", "Little Rabbit.", "The fish."], 1, "M3U1·story result", 35),
        ],
        "Animal School has no classrooms. There is a big forest and a small river. Little Rabbit is sad because it can't swim or climb trees. Mr Owl says, 'I don't think you are a bad student. Come on! Have a try!' Little Rabbit runs very fast. It is first, and now it is happy.",
        [
            passage_question(17, "Animal School has a big forest.", "true", "M3U1·forest", 35),
            passage_question(18, "Little Rabbit can swim well.", "false", "M3U1·can't swim", 35, "原文是can't swim"),
            passage_question(19, "Mr Owl asks Little Rabbit to try.", "true", "M3U1·Have a try", 35),
            passage_question(20, "Little Rabbit is last in the race.", "false", "M3U1·first", 35, "原文是first"),
        ],
    ),
    listening_course(
        35,
        "听力周测卷 · M3U1 In our school",
        "4A M3U1 教材第32-36页综合：学校、There is/are、Animal School、fr/gr/tr + 已学旧坑复现",
        36,
        [
            word(1, "fruit", ["fruit", "floor", "front"], 0, "M3U1·fr sound", 36),
            word(2, "grandpa", ["garden", "grandpa", "grandma"], 1, "M3U1·gr sound", 36),
            word(3, "tree", ["try", "tidy", "tree"], 2, "M3U1·tr sound", 36),
            word(4, "bookshelf", ["bookshelf", "schoolbag", "building"], 0, "M3U1·classroom", 36),
        ],
        [
            sentence(5, "There is a hall in our school.", "There is a hall in our school.", "same", "M3U1·school survey", 36),
            sentence(6, "There are some desks in the classroom.", "There are some chairs in the classroom.", "different", "M3U1·There are", 36, "原文是chairs"),
            sentence(7, "Grandpa grows the fruit.", "Grandpa grows the fruit.", "same", "M3U1·gr/fr sounds", 36),
            sentence(8, "These are my notebooks.", "This is my notebook.", "different", "旧坑复现·this/these", 36, "原文是This is"),
        ],
        [
            response(9, "What's in your school?", ["There is a hall.", "It is a hall.", "I can run."], 0, "M3U1·school survey", 36),
            response(10, "What's in your classroom?", ["There are some desks and chairs.", "There are some pencils.", "There is some fruit."], 0, "M3U1·classroom survey", 36),
            response(11, "What's in your schoolbag?", ["There are some notebooks.", "There is a gym.", "There are some trees."], 0, "M3U1·schoolbag survey", 36),
            response(12, "Can Little Rabbit run fast?", ["Yes, it can.", "Yes, it is.", "Yes, it does."], 0, "旧坑复现·can question", 36),
        ],
        [
            dialogue(13, [("f", "What's in your school?"), ("m", "There is a hall, a library and a playground.")], "Is there a library?", ["Yes, there is.", "No, there isn't.", "Yes, it can."], 0, "M3U1·school survey", 36),
            dialogue(14, [("m", "What's in your classroom?"), ("f", "There is a cupboard and a bookshelf.")], "What is in the classroom?", ["A swing and a slide.", "A cupboard and a bookshelf.", "A canteen and a gym."], 1, "M3U1·classroom survey", 36),
            dialogue(15, [("f", "Where is the playground?"), ("m", "It is behind the classroom building.")], "Where is the playground?", ["Behind the classroom building.", "In front of the garden.", "On this floor."], 0, "M3U1·behind", 36),
            dialogue(16, [("m", "What's the matter, Little Rabbit?"), ("f", "I'm sad. I can't swim, but I can run fast.")], "What can Little Rabbit do?", ["Swim well.", "Climb trees.", "Run fast."], 2, "旧坑复现·can/can't", 36),
        ],
        "Welcome to our school. There is a hall, a library and a playground. The playground is behind the classroom building. In our classroom, there is a cupboard and a bookshelf. There are some desks and chairs. In my schoolbag, there are some pencils and notebooks. Grandpa grows fruit on the trees. Little Rabbit can't swim, but it can run fast.",
        [
            passage_question(17, "There is a library in the school.", "true", "周测·school place", 36),
            passage_question(18, "The playground is in front of the classroom building.", "false", "周测·behind", 36, "原文是behind"),
            passage_question(19, "There are some pencils and notebooks in the schoolbag.", "true", "周测·schoolbag", 36),
            passage_question(20, "Little Rabbit can swim well.", "false", "周测·can/can't", 36, "原文是can't swim"),
        ],
    ),
]


SPEAKING = [
    speaking_course(
        31,
        "口语练习 · M3U1 School places",
        [
            repeat(1, "This is our canteen.", 32),
            repeat(2, "This is the computer lab.", 32),
            repeat(3, "This is the teachers' office.", 32),
            repeat(4, "This is our gym.", 32),
            repeat(5, "The gym is behind the office.", 32),
            repeat(6, "The computer lab is in front of the gym.", 32),
            qa(7, "What is this?", "It is a canteen.", "用英语说：这是食堂。", 32),
            qa(8, "Where is the gym?", "It is behind the office.", "用英语说：它在办公室后面。", 32),
        ],
    ),
    speaking_course(
        32,
        "口语练习 · M3U1 In our school",
        [
            repeat(1, "This is our classroom building.", 33),
            repeat(2, "There is a teachers' office.", 33),
            repeat(3, "There are some computers.", 33),
            repeat(4, "There is a library.", 33),
            repeat(5, "We have lunch in the canteen.", 33),
            repeat(6, "The playground is behind the classroom building.", 33),
            qa(7, "What's in the computer lab?", "There are some computers.", "用英语说：有一些电脑。", 33),
            qa(8, "Where do you have lunch?", "We have lunch in the canteen.", "用英语说：我们在食堂吃午饭。", 33),
        ],
    ),
    speaking_course(
        33,
        "口语练习 · A visit to Rainbow Primary School",
        [
            repeat(1, "Welcome to Rainbow Primary School.", 34),
            repeat(2, "The garden is in front of the classroom building.", 34),
            repeat(3, "What's on this floor?", 34),
            repeat(4, "There is a computer lab.", 34),
            repeat(5, "Our classroom is clean and tidy.", 34),
            repeat(6, "Thank you. You're welcome.", 34),
            qa(7, "What's in the garden?", "There are some flowers and plants.", "用英语说：有一些花和植物。", 34),
            qa(8, "How is your classroom?", "It is clean and tidy.", "用英语说：它干净又整洁。", 34),
        ],
    ),
    speaking_course(
        34,
        "口语练习 · Animal School",
        [
            repeat(1, "There are no classrooms in Animal School.", 35),
            repeat(2, "What's the matter?", 35),
            repeat(3, "I'm sad. I can't swim.", 35),
            repeat(4, "I don't think so.", 35),
            repeat(5, "Come on! Have a try!", 35),
            repeat(6, "Little Rabbit can run fast.", 35),
            qa(7, "Can Little Rabbit swim?", "No, it can't.", "用英语说：不，它不会。", 35),
            qa(8, "What can Little Rabbit do?", "It can run fast.", "用英语说：它能跑得很快。", 35),
        ],
    ),
    speaking_course(
        35,
        "口语周复习 · M3U1 In our school",
        [
            repeat(1, "What's in your school?", 36),
            repeat(2, "There is a hall and a library.", 36),
            repeat(3, "What's in your classroom?", 36),
            repeat(4, "There is a cupboard and a bookshelf.", 36),
            repeat(5, "Grandpa grows the fruit.", 36),
            repeat(6, "The fruit is on the trees.", 36),
            qa(7, "What's in your schoolbag?", "There are some pencils and notebooks.", "用英语说：有一些铅笔和练习本。", 36),
            qa(8, "Where is the playground?", "It is behind the classroom building.", "用英语说：它在教学楼后面。", 36),
        ],
    ),
]


def write_json(course, directory):
    path = directory / f"{course['course_id']}.json"
    path.write_text(json.dumps(course, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def transcript_text(parts):
    return " / ".join(text for _, text in parts)


def listening_parent_doc(courses):
    lines = [
        "# W01D31-35 听力答案与原文（家长版）",
        "",
        "> 生成日期：2026-08-06  ",
        "> 对齐规则：W/S 同课同页；本批只覆盖已学完的 4A M3U1 第32-36页，不进入 M3U2。  ",
        "> 内容比例：约80% M3U1 + 约20% 已学旧坑复现。",
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
                lines.append(f"- 短文原文：{transcript_text(section['passage_transcript'])}")
            for question in section["questions"]:
                page_note = question["parent_note"]
                if question["type"] == "word_choice":
                    answer = question["options"][question["answer"]]
                    lines.append(f"- Q{question['id']:02d} 原文：{transcript_text(question['transcript'])}｜答案：{answer}｜{page_note}")
                elif question["type"] == "sentence_judge":
                    answer = "相同" if question["answer"] == "same" else "不同"
                    lines.append(f"- Q{question['id']:02d} 屏显：{question['display']}｜原文：{transcript_text(question['transcript'])}｜答案：{answer}｜{page_note}")
                elif question["type"] == "question_response":
                    answer = question["options"][question["answer"]]
                    lines.append(f"- Q{question['id']:02d} 原文：{transcript_text(question['transcript'])}｜答案：{answer}｜{page_note}")
                elif question["type"] == "dialogue_choice":
                    answer = question["options"][question["answer"]]
                    lines.append(f"- Q{question['id']:02d} 原文：{transcript_text(question['transcript'])}｜答案：{answer}｜{page_note}")
                else:
                    answer = "正确" if question["answer"] == "true" else "错误"
                    lines.append(f"- Q{question['id']:02d} 判断：{question['statement']}｜答案：{answer}｜{page_note}")
            lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def speaking_parent_doc(courses):
    lines = [
        "# S01D31-35 口语课文与答案（家长版）",
        "",
        "> 生成日期：2026-08-06  ",
        "> 规则：每课8题，6题 repeat + 2题 qa；与同编号听力课程逐页对齐，不进入 M3U2。",
        "",
    ]
    for course in courses:
        lines.append(f"## {course['course_id']} · {course['title']}")
        lines.append("")
        for question in course["questions"]:
            if question["type"] == "repeat":
                lines.append(f"- Q{question['id']:02d} 跟读：{question['text']}｜{question['parent_note']}")
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
    (PARENT_DIR / "W01D31-35_听力答案与原文_家长版.md").write_text(
        listening_parent_doc(LISTENING), encoding="utf-8"
    )
    (PARENT_DIR / "S01D31-35_口语课文与答案_家长版.md").write_text(
        speaking_parent_doc(SPEAKING), encoding="utf-8"
    )
    print("Built 5 listening courses, 5 speaking courses, and 2 parent documents.")


if __name__ == "__main__":
    main()
