# -*- coding: utf-8 -*-
"""Build paired cumulative review courses W/S01D41-D50."""
import json
import os


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LISTENING_DIR = os.path.join(ROOT, "content", "listening")
SPEAKING_DIR = os.path.join(ROOT, "content", "speaking")
OPEN_DATE = "2026-08-16"


def _question(section, qid, qtype, payload, course_id):
    item = {
        "id": qid,
        "type": qtype,
        "tag": "%s·综合复习" % section,
        "parent_note": "4A M1U1-M3U2 已学内容复现",
    }
    item.update(payload)
    if qtype != "passage_judge":
        item["audio"] = "static/audio/listening/%s/q%02d.mp3" % (course_id, qid)
    return item


def build_listening(number, spec):
    course_id = "W01D%02d" % number
    sections = []

    questions = []
    for qid, (spoken, options, answer) in enumerate(spec["words"], 1):
        questions.append(_question(
            spec["scope"], qid, "word_choice",
            {"options": options, "answer": answer, "transcript": [["n", spoken]]},
            course_id,
        ))
    sections.append({
        "id": "word_discrimination", "name": "听音选词",
        "tip": "听录音，选出你听到的单词", "max_plays": 2,
        "questions": questions,
    })

    questions = []
    for qid, (spoken, display, answer) in enumerate(spec["sentences"], 5):
        questions.append(_question(
            spec["scope"], qid, "sentence_judge",
            {"display": display, "answer": answer, "transcript": [["n", spoken]]},
            course_id,
        ))
    sections.append({
        "id": "sentence_meaning", "name": "听句判断",
        "tip": "听句子，判断和屏幕上句子的意思是不是一样", "max_plays": 2,
        "questions": questions,
    })

    questions = []
    for qid, (spoken, options, answer) in enumerate(spec["responses"], 9):
        questions.append(_question(
            spec["scope"], qid, "question_response",
            {"options": options, "answer": answer, "transcript": [["n", spoken]]},
            course_id,
        ))
    sections.append({
        "id": "question_response", "name": "听问句选答语",
        "tip": "听问句，选出最合适的回答", "max_plays": 2,
        "questions": questions,
    })

    questions = []
    for qid, (clips, question_text, options, answer) in enumerate(spec["dialogues"], 13):
        transcript = list(clips) + [["n", "Question: " + question_text]]
        questions.append(_question(
            spec["scope"], qid, "dialogue_choice",
            {
                "question_text": question_text,
                "options": options,
                "answer": answer,
                "transcript": transcript,
            },
            course_id,
        ))
    sections.append({
        "id": "dialogue", "name": "听对话选答案",
        "tip": "听短对话和问题，选出正确答案", "max_plays": 2,
        "questions": questions,
    })

    questions = []
    for qid, (statement, answer) in enumerate(spec["statements"], 17):
        questions.append(_question(
            spec["scope"], qid, "passage_judge",
            {"statement": statement, "answer": answer},
            course_id,
        ))
    sections.append({
        "id": "passage", "name": "听短文判断",
        "tip": "先听短文，再判断四句话是否正确", "max_plays": 3,
        "shared_audio": True,
        "passage_audio": "static/audio/listening/%s/p01.mp3" % course_id,
        "passage_transcript": spec["passage"],
        "questions": questions,
    })

    return {
        "course_id": course_id,
        "title": ("听力综合测评 · " if number >= 49 else "听力复习 · ") + spec["title"],
        "week": 6,
        "day": number - 40,
        "course_type": "weekly_test" if number >= 49 else "training",
        "est_minutes": 20,
        "scope": "%s：%s" % (spec["scope"], spec["focus"]),
        "difficulty": "L1",
        "open_date": OPEN_DATE,
        "scoring": {"per_question": 5, "total": 100},
        "test_audio": "static/audio/listening/%s/hello.mp3" % course_id,
        "test_transcript": [["n", "Hello! Can you hear me? Let's begin."]],
        "sections": sections,
    }


def build_speaking(number, spec):
    course_id = "S01D%02d" % number
    questions = []
    for qid, text in enumerate(spec["repeats"], 1):
        questions.append({
            "id": qid, "type": "repeat", "text": text,
            "audio": "static/audio/speaking/%s/q%02d.mp3" % (course_id, qid),
            "tag": "%s·综合复习" % spec["scope"],
            "parent_note": "4A M1U1-M3U2 已学内容复现",
        })
    for qid, (question, expected, hint) in enumerate(spec["qa"], 7):
        questions.append({
            "id": qid, "type": "qa", "question": question,
            "expected": expected, "hint": hint,
            "audio": "static/audio/speaking/%s/q%02d.mp3" % (course_id, qid),
            "tag": "%s·综合复习" % spec["scope"],
            "parent_note": "固定答案跟读式问答，不采集真实个人信息",
        })
    return {
        "course_id": course_id,
        "title": ("口语综合测评 · " if number >= 49 else "口语复习 · ") + spec["title"],
        "week": 6,
        "day": number - 40,
        "course_type": "weekly_review" if number >= 49 else "training",
        "est_minutes": 8,
        "scope": "%s：%s" % (spec["scope"], spec["focus"]),
        "difficulty": "L1",
        "open_date": OPEN_DATE,
        "questions": questions,
    }


LISTENING = {
    41: {
        "scope": "M1U1", "title": "Meeting new people",
        "focus": "人物介绍、姓名、年龄、学号和my/your/his/her",
        "words": [
            ("classmate", ["classmate", "classroom", "teacher"], 0),
            ("eleven", ["seven", "eleven", "twelve"], 1),
            ("student", ["student", "street", "school"], 0),
            ("number", ["name", "number", "mother"], 1),
        ],
        "sentences": [
            ("This is my new classmate.", "This is my new classmate.", "same"),
            ("Her name is Jill.", "His name is Jill.", "different"),
            ("My student number is fourteen.", "My student number is fourteen.", "same"),
            ("Jill lives near our school.", "Jill lives far from our school.", "different"),
        ],
        "responses": [
            ("What's your name?", ["My name is Alice.", "I'm ten.", "It's twelve."], 0),
            ("How old are you?", ["I'm a student.", "I'm ten.", "I'm Alice."], 1),
            ("What's your student number?", ["It's thirteen.", "I'm thirteen.", "He's thirteen."], 0),
            ("Who is she?", ["She's my classmate.", "He's my classmate.", "I'm her classmate."], 0),
        ],
        "dialogues": [
            ([["f", "This is my friend, Jill."], ["m", "Hello, Jill."]], "Who is Jill?", ["A friend.", "A teacher.", "A doctor."], 0),
            ([["f", "What's his name?"], ["m", "His name is Joe."]], "What is the boy's name?", ["Jill.", "Joe.", "Peter."], 1),
            ([["m", "How old is Kitty?"], ["f", "She is eleven."]], "How old is Kitty?", ["Ten.", "Eleven.", "Twelve."], 1),
            ([["f", "Does Jill walk to school?"], ["m", "Yes, she does."]], "How does Jill go to school?", ["She walks.", "She runs.", "She swims."], 0),
        ],
        "passage": [["n", "This is Alice. She is ten. Her student number is fifteen. Peter is her classmate. He is eleven. His student number is twelve."]],
        "statements": [("Alice is ten.", "true"), ("Alice's student number is twelve.", "false"), ("Peter is Alice's classmate.", "true"), ("Peter is eleven.", "true")],
    },
    42: {
        "scope": "M1U2", "title": "Abilities",
        "focus": "能力动词、can加动词原形和一般疑问句",
        "words": [
            ("draw", ["draw", "dance", "drink"], 0),
            ("write", ["read", "ride", "write"], 2),
            ("swim", ["skip", "swim", "sing"], 1),
            ("jump", ["run", "jump", "paint"], 1),
        ],
        "sentences": [
            ("I can paint a picture.", "I can paint a picture.", "same"),
            ("She can swim well.", "She can swims well.", "different"),
            ("He can run fast.", "He can run fast.", "same"),
            ("The bird can fly high.", "The bird can jump high.", "different"),
        ],
        "responses": [
            ("What can you do?", ["I can draw.", "Yes, I can.", "I like drawing."], 0),
            ("Can she swim?", ["Yes, she does.", "Yes, she can.", "Yes, she is."], 1),
            ("Can the fish fly?", ["No, it can't.", "No, it doesn't.", "No, it isn't."], 0),
            ("What can he do?", ["He can run.", "She can run.", "He likes running."], 0),
        ],
        "dialogues": [
            ([["f", "Can you draw, Ben?"], ["m", "Yes. I can draw a robot."]], "What can Ben draw?", ["A robot.", "A flower.", "A tree."], 0),
            ([["m", "Can Jill swim?"], ["f", "No, but she can jump."]], "What can Jill do?", ["Swim.", "Jump.", "Fly."], 1),
            ([["f", "What can Peter do?"], ["m", "He can read and write."]], "Can Peter write?", ["Yes, he can.", "No, he can't.", "We don't know."], 0),
            ([["m", "Can this bird run?"], ["f", "No. It can fly high."]], "What can the bird do?", ["Run fast.", "Swim well.", "Fly high."], 2),
        ],
        "passage": [["n", "Alice can read and write. She likes drawing. Ben can run fast, but he cannot swim. Their little bird can fly high."]],
        "statements": [("Alice can read.", "true"), ("Alice likes swimming.", "false"), ("Ben can swim.", "false"), ("The bird can fly high.", "true")],
    },
    43: {
        "scope": "M1U3", "title": "How do you feel?",
        "focus": "感受、How do you feel和礼貌表达",
        "words": [
            ("hungry", ["hungry", "happy", "thirsty"], 0),
            ("thirsty", ["thirty", "thirsty", "tired"], 1),
            ("tired", ["sad", "tired", "full"], 1),
            ("biscuit", ["biscuit", "basket", "butter"], 0),
        ],
        "sentences": [
            ("I'm hungry.", "I'm hungry.", "same"),
            ("She's thirsty.", "She's tired.", "different"),
            ("Have some water.", "Have some water.", "same"),
            ("We are full now.", "We are hungry now.", "different"),
        ],
        "responses": [
            ("How do you feel?", ["I'm thirsty.", "I can drink.", "I have water."], 0),
            ("Have some biscuits.", ["Thank you.", "I'm sorry.", "Yes, I am."], 0),
            ("Are you tired?", ["Yes, I am.", "Yes, I do.", "Yes, I can."], 0),
            ("Are you hungry?", ["No, I'm not.", "No, I don't.", "No, I can't."], 0),
        ],
        "dialogues": [
            ([["f", "I'm thirsty."], ["m", "Have some water."], ["f", "Thank you."]], "What does the girl need?", ["Water.", "A book.", "A ball."], 0),
            ([["m", "How do you feel, Jill?"], ["f", "I'm tired."]], "How does Jill feel?", ["Happy.", "Tired.", "Full."], 1),
            ([["f", "Are you hungry?"], ["m", "No. I'm full."]], "Is the boy hungry?", ["Yes, he is.", "No, he isn't.", "We don't know."], 1),
            ([["m", "Ginger is sad."], ["f", "I have an idea. I can help."]], "Who has an idea?", ["The girl.", "The boy.", "Ginger."], 0),
        ],
        "passage": [["n", "Kitty is hungry, so she has a biscuit. Ben is thirsty, so he drinks some water. Now Kitty is full and Ben is happy."]],
        "statements": [("Kitty is hungry at first.", "true"), ("Kitty has some water.", "false"), ("Ben drinks water.", "true"), ("Ben is sad at the end.", "false")],
    },
    44: {
        "scope": "M2U1", "title": "Jill's family",
        "focus": "家庭成员、have/has、年龄和能力",
        "words": [
            ("uncle", ["uncle", "aunt", "cousin"], 0),
            ("aunt", ["uncle", "aunt", "mother"], 1),
            ("cousin", ["cousin", "classmate", "sister"], 0),
            ("police officer", ["bus driver", "police officer", "firefighter"], 1),
        ],
        "sentences": [
            ("This is my uncle.", "This is my uncle.", "same"),
            ("She has a cousin.", "She have a cousin.", "different"),
            ("My aunt is thirty-five years old.", "My aunt is thirty-five years old.", "same"),
            ("His uncle can run fast.", "Her uncle can swim well.", "different"),
        ],
        "responses": [
            ("Do you have an uncle?", ["Yes, I do.", "Yes, I have.", "Yes, I am."], 0),
            ("Who's that woman?", ["She's my aunt.", "He's my uncle.", "It's my cousin."], 0),
            ("How old is your cousin?", ["She's twelve.", "She's a student.", "She's my cousin."], 0),
            ("What can your uncle do?", ["He can run fast.", "He is tall.", "He likes running."], 0),
        ],
        "dialogues": [
            ([["f", "Who's that man?"], ["m", "He's my uncle."]], "Who is the man?", ["An uncle.", "A father.", "A cousin."], 0),
            ([["m", "Do you have a cousin?"], ["f", "Yes. Her name is Jill."]], "What is the cousin's name?", ["Kitty.", "Jill.", "Alice."], 1),
            ([["f", "How old is Joe?"], ["m", "He is twelve years old."]], "How old is Joe?", ["Eleven.", "Twelve.", "Thirteen."], 1),
            ([["m", "What does your uncle do?"], ["f", "He is a police officer."]], "What is the uncle's job?", ["A teacher.", "A police officer.", "A doctor."], 1),
        ],
        "passage": [["n", "This is Jill's family photo. Her uncle is a police officer. He can run fast. Her aunt likes reading. Jill has a cousin. His name is Dan and he is twelve."]],
        "statements": [("Jill's uncle is a police officer.", "true"), ("Her uncle can swim well.", "false"), ("Her aunt likes reading.", "true"), ("Dan is eleven.", "false")],
    },
    45: {
        "scope": "M2U2", "title": "Jobs",
        "focus": "职业、What does ... do和职业地点",
        "words": [
            ("firefighter", ["firefighter", "teacher", "doctor"], 0),
            ("nurse", ["nurse", "teacher", "driver"], 0),
            ("doctor", ["doctor", "daughter", "driver"], 0),
            ("bus driver", ["police officer", "bus driver", "firefighter"], 1),
        ],
        "sentences": [
            ("Her father is a firefighter.", "Her father is a firefighter.", "same"),
            ("Mrs White is a teacher.", "Mrs White is a nurse.", "different"),
            ("The doctor works in a hospital.", "The doctor works in a hospital.", "same"),
            ("Mr Li drives a bus.", "Mr Li drives a fire engine.", "different"),
        ],
        "responses": [
            ("What does your mother do?", ["She is a nurse.", "She can help.", "She likes reading."], 0),
            ("Is he a firefighter?", ["Yes, he is.", "Yes, he does.", "Yes, he can."], 0),
            ("Where does the teacher work?", ["At a school.", "In a fire station.", "On a bus."], 0),
            ("What can a firefighter do?", ["Put out a fire.", "Teach English.", "Drive a school bus."], 0),
        ],
        "dialogues": [
            ([["f", "What does Jill's mother do?"], ["m", "She is a nurse."]], "What is Jill's mother's job?", ["A nurse.", "A teacher.", "A doctor."], 0),
            ([["m", "Is Mr Black a police officer?"], ["f", "No. He is a firefighter."]], "What does Mr Black do?", ["He is a police officer.", "He is a firefighter.", "He is a doctor."], 1),
            ([["f", "Who is the bus driver?"], ["m", "Mr Li is the bus driver."]], "Who drives the bus?", ["Mr Li.", "Mrs Li.", "Jill."], 0),
            ([["m", "Does your father work at a school?"], ["f", "Yes. He is a teacher."]], "Where does the father work?", ["At a school.", "At a hospital.", "At a fire station."], 0),
        ],
        "passage": [["n", "Peter's father is a teacher. He works at a school. His mother is a doctor. She works in a hospital. Jill's father is a firefighter and her mother is a nurse."]],
        "statements": [("Peter's father is a teacher.", "true"), ("Peter's mother is a nurse.", "false"), ("Jill's father is a firefighter.", "true"), ("Jill's mother is a doctor.", "false")],
    },
    46: {
        "scope": "M2U3", "title": "Friends",
        "focus": "朋友、衣着、外貌和has/can/likes",
        "words": [
            ("shirt", ["shirt", "skirt", "shorts"], 0),
            ("dress", ["dress", "draw", "driver"], 0),
            ("shorts", ["shirt", "shorts", "shoes"], 1),
            ("friend", ["friend", "front", "fireman"], 0),
        ],
        "sentences": [
            ("My friend has a blue T-shirt.", "My friend has a blue T-shirt.", "same"),
            ("She has long hair.", "She has short hair.", "different"),
            ("He can ride a bicycle.", "He can ride a bicycle.", "same"),
            ("Kitty likes dancing.", "Kitty likes dance.", "different"),
        ],
        "responses": [
            ("Who is your friend?", ["Peter is my friend.", "He is tall.", "He can swim."], 0),
            ("What does she have?", ["She has a red dress.", "She is in red.", "She likes red."], 0),
            ("What can he do?", ["He can ride a bicycle.", "He has a bicycle.", "He likes bicycles."], 0),
            ("What does Kitty like doing?", ["She likes dancing.", "She can dance.", "She has a dress."], 0),
        ],
        "dialogues": [
            ([["f", "Who is that boy?"], ["m", "He is my friend, Tom."]], "What is the boy's name?", ["Tom.", "Ben.", "Joe."], 0),
            ([["m", "What does Alice have?"], ["f", "She has a green dress."]], "What colour is Alice's dress?", ["Red.", "Green.", "Blue."], 1),
            ([["f", "Can your friend swim?"], ["m", "No, but he can run fast."]], "What can the friend do?", ["Swim.", "Run fast.", "Fly."], 1),
            ([["m", "Does Jill like reading?"], ["f", "Yes. She reads every evening."]], "What does Jill like doing?", ["Reading.", "Dancing.", "Swimming."], 0),
        ],
        "passage": [["n", "I have a friend. Her name is Alice. She has long hair and a yellow dress. She can draw well and she likes reading. She walks to school with me."]],
        "statements": [("The friend's name is Alice.", "true"), ("Alice has short hair.", "false"), ("Alice can draw well.", "true"), ("Alice likes swimming.", "false")],
    },
    47: {
        "scope": "M3U1", "title": "In our school",
        "focus": "学校地点、There is/are和方位表达",
        "words": [
            ("library", ["library", "classroom", "playground"], 0),
            ("office", ["office", "hall", "toilet"], 0),
            ("playground", ["classroom", "playground", "school"], 1),
            ("behind", ["behind", "between", "beside"], 0),
        ],
        "sentences": [
            ("There is a library in our school.", "There is a library in our school.", "same"),
            ("The playground is behind the classroom building.", "The playground is in front of the classroom building.", "different"),
            ("There are many books in the library.", "There are many books in the library.", "same"),
            ("The teachers' office is on the first floor.", "The teachers' office is on the second floor.", "different"),
        ],
        "responses": [
            ("Is there a library in your school?", ["Yes, there is.", "Yes, it is.", "Yes, there are."], 0),
            ("Are there any classrooms?", ["Yes, there are.", "Yes, there is.", "Yes, they are."], 0),
            ("Where is the playground?", ["It is behind the hall.", "There are two playgrounds.", "I can run there."], 0),
            ("What can you do in the library?", ["I can read books.", "I can play football.", "I can swim."], 0),
        ],
        "dialogues": [
            ([["f", "Where is the library?"], ["m", "It is behind the classroom building."]], "Where is the library?", ["Behind the classroom building.", "In front of the gate.", "Next to the playground."], 0),
            ([["m", "Is there a computer room?"], ["f", "Yes. It is on the second floor."]], "Where is the computer room?", ["On the first floor.", "On the second floor.", "Behind the school."], 1),
            ([["f", "How many classrooms are there?"], ["m", "There are twelve classrooms."]], "How many classrooms are there?", ["Ten.", "Eleven.", "Twelve."], 2),
            ([["m", "What can you do in the playground?"], ["f", "We can run and play football."]], "Can the children run there?", ["Yes, they can.", "No, they can't.", "We don't know."], 0),
        ],
        "passage": [["n", "Our school is big. There is a library behind the classroom building. There are many books in it. The playground is in front of the hall. We can run and play there."]],
        "statements": [("The school is big.", "true"), ("The library is in front of the classroom building.", "false"), ("There are many books in the library.", "true"), ("The playground is behind the hall.", "false")],
    },
    48: {
        "scope": "M3U2", "title": "Around my home",
        "focus": "社区地点、next to/between和位置问答",
        "words": [
            ("supermarket", ["supermarket", "restaurant", "post office"], 0),
            ("restaurant", ["restaurant", "supermarket", "bakery"], 0),
            ("post office", ["police office", "post office", "teachers' office"], 1),
            ("between", ["behind", "between", "in front of"], 1),
        ],
        "sentences": [
            ("There is a supermarket near my home.", "There is a supermarket near my home.", "same"),
            ("The bakery is next to the post office.", "The bakery is behind the post office.", "different"),
            ("The restaurant is between the hotel and the shop.", "The restaurant is between the hotel and the shop.", "same"),
            ("Nanjing Road is very busy.", "Nanjing Road is very quiet.", "different"),
        ],
        "responses": [
            ("Where is the supermarket?", ["It is next to the park.", "There is a supermarket.", "I go there."], 0),
            ("Is there a post office near here?", ["Yes, there is.", "Yes, it is.", "Yes, there are."], 0),
            ("Are there any restaurants?", ["Yes, there are.", "Yes, there is.", "Yes, they are."], 0),
            ("Where is the bakery?", ["It is between two shops.", "It has bread.", "I like the bakery."], 0),
        ],
        "dialogues": [
            ([["f", "Excuse me. Where is the post office?"], ["m", "It is next to the supermarket."]], "Where is the post office?", ["Next to the supermarket.", "Behind the school.", "Between two parks."], 0),
            ([["m", "Is there a restaurant near your home?"], ["f", "Yes. It is on Garden Street."]], "What is on Garden Street?", ["A restaurant.", "A school.", "A library."], 0),
            ([["f", "Where is the bakery?"], ["m", "It is between the hotel and the clothes shop."]], "What is next to the bakery?", ["A hotel and a clothes shop.", "A school and a park.", "Two supermarkets."], 0),
            ([["m", "Can you show me the way?"], ["f", "Yes. The supermarket is over there."], ["m", "Thank you."], ["f", "It's my pleasure."]], "Where does the man want to go?", ["The supermarket.", "The library.", "The school."], 0),
        ],
        "passage": [["n", "I live on Garden Street. There is a supermarket next to my home. A bakery is between the supermarket and a post office. There are two restaurants near the park."]],
        "statements": [("The child lives on Garden Street.", "true"), ("The supermarket is far from the home.", "false"), ("The bakery is between two places.", "true"), ("There is only one restaurant near the park.", "false")],
    },
    49: {
        "scope": "M1-M2", "title": "People and families",
        "focus": "人物、感受、家庭、职业和能力综合复习",
        "words": [
            ("classmate", ["classmate", "cousin", "teacher"], 0),
            ("thirsty", ["thirsty", "thirty", "tired"], 0),
            ("firefighter", ["firefighter", "police officer", "bus driver"], 0),
            ("cousin", ["uncle", "cousin", "friend"], 1),
        ],
        "sentences": [
            ("Her name is Jill.", "His name is Jill.", "different"),
            ("He can swim well.", "He can swim well.", "same"),
            ("My aunt likes reading.", "My aunt likes read.", "different"),
            ("Peter has a blue shirt.", "Peter has a blue shirt.", "same"),
        ],
        "responses": [
            ("How do you feel?", ["I'm hungry.", "I can cook.", "I have a biscuit."], 0),
            ("What can she do?", ["She can draw.", "She is a nurse.", "She likes drawing."], 0),
            ("What does his father do?", ["He is a doctor.", "He can help people.", "He works in a hospital."], 0),
            ("Do you have a cousin?", ["Yes, I do.", "Yes, I am.", "Yes, I can."], 0),
        ],
        "dialogues": [
            ([["f", "This is my cousin, Joe."], ["m", "How old is he?"], ["f", "He is twelve."]], "How old is Joe?", ["Eleven.", "Twelve.", "Thirteen."], 1),
            ([["m", "What can Alice do?"], ["f", "She can paint and draw."]], "Can Alice draw?", ["Yes, she can.", "No, she can't.", "We don't know."], 0),
            ([["f", "How does Ben feel?"], ["m", "He is thirsty."], ["f", "Have some water, Ben."]], "What does Ben need?", ["Water.", "A shirt.", "A book."], 0),
            ([["m", "What does Jill's mother do?"], ["f", "She is a nurse and she works in a hospital."]], "Where does Jill's mother work?", ["In a hospital.", "At a school.", "On a bus."], 0),
        ],
        "passage": [["n", "This is my friend Jill. She is eleven and her student number is sixteen. She can draw well and she likes reading. Her mother is a nurse. Jill has a cousin. His name is Dan."]],
        "statements": [("Jill is eleven.", "true"), ("Her student number is fifteen.", "false"), ("Jill likes reading.", "true"), ("Jill's mother is a teacher.", "false")],
    },
    50: {
        "scope": "M1-M3U2", "title": "Full review",
        "focus": "人物、能力、感受、家庭、学校和社区总复习",
        "words": [
            ("present", ["present", "parent", "restaurant"], 0),
            ("bitter", ["bitter", "butter", "better"], 0),
            ("library", ["library", "bakery", "hospital"], 0),
            ("between", ["behind", "between", "next to"], 1),
        ],
        "sentences": [
            ("This is an aeroplane.", "This is a aeroplane.", "different"),
            ("These are my books.", "These are my books.", "same"),
            ("A dog has four legs.", "A dog have four legs.", "different"),
            ("There are two shops near the school.", "There are two shops near the school.", "same"),
        ],
        "responses": [
            ("What's your student number?", ["It's fourteen.", "I'm fourteen.", "She's fourteen."], 0),
            ("Can the bird fly high?", ["Yes, it can.", "Yes, it does.", "Yes, it is."], 0),
            ("Are there any classrooms?", ["Yes, there are.", "Yes, there is.", "Yes, they are."], 0),
            ("Where is the post office?", ["It is next to the bakery.", "There is one post office.", "I can show you."], 0),
        ],
        "dialogues": [
            ([["f", "Who is that girl?"], ["m", "She is my classmate. Her name is Alice."]], "What is the girl's name?", ["Alice.", "Jill.", "Kitty."], 0),
            ([["m", "Are you hungry?"], ["f", "No, I'm full, but I am thirsty."]], "How does the girl feel?", ["Thirsty.", "Hungry.", "Sad."], 0),
            ([["f", "Where is the library?"], ["m", "It is behind the hall."]], "What is in front of the library?", ["The hall.", "The playground.", "The office."], 0),
            ([["m", "Is there a supermarket near your home?"], ["f", "Yes. It is next to a restaurant."]], "What is next to the supermarket?", ["A restaurant.", "A school.", "A hospital."], 0),
        ],
        "passage": [["n", "Alice is my classmate. She is eleven and she can swim well. Her father is a teacher. Alice's school has a library and a big playground. There is a supermarket next to her home and a bakery near the park."]],
        "statements": [("Alice is eleven.", "true"), ("Alice cannot swim.", "false"), ("Her father is a teacher.", "true"), ("The bakery is next to her home.", "false")],
    },
}


SPEAKING = {
    41: {
        "scope": "M1U1", "title": "Meeting new people",
        "focus": "人物介绍、姓名、年龄和学号",
        "repeats": [
            "This is my new classmate.", "Her name is Jill.",
            "His name is Joe.", "She is eleven years old.",
            "Her student number is sixteen.", "Jill walks to school.",
        ],
        "qa": [
            ("What's her name?", "Her name is Jill.", "用英语说：她的名字叫 Jill。"),
            ("What's her student number?", "Her student number is sixteen.", "用英语说：她的学号是十六。"),
        ],
    },
    42: {
        "scope": "M1U2", "title": "Abilities",
        "focus": "能力动词和can问答",
        "repeats": [
            "I can read and write.", "She can draw a flower.",
            "He can run fast.", "The fish can swim well.",
            "The bird can fly high.", "She cannot jump high.",
        ],
        "qa": [
            ("What can Alice do?", "She can draw.", "用英语说：她会画画。"),
            ("Can the fish fly?", "No, it can't.", "用英语说：不，它不会。"),
        ],
    },
    43: {
        "scope": "M1U3", "title": "How do you feel?",
        "focus": "感受和礼貌表达",
        "repeats": [
            "I'm hungry.", "She's thirsty.", "He is tired.",
            "Have some water.", "Thank you very much.", "I have an idea.",
        ],
        "qa": [
            ("How does Jill feel?", "She's thirsty.", "用英语说：她口渴。"),
            ("Are you hungry?", "No, I'm not.", "用英语说：不，我不饿。"),
        ],
    },
    44: {
        "scope": "M2U1", "title": "Jill's family",
        "focus": "家庭成员、年龄和能力",
        "repeats": [
            "This is my uncle.", "She is my aunt.", "I have a cousin.",
            "My uncle is a police officer.", "He is thirty-five years old.",
            "My cousin can swim well.",
        ],
        "qa": [
            ("Who's that woman?", "She's my aunt.", "用英语说：她是我的阿姨。"),
            ("Do you have a cousin?", "Yes, I do.", "用英语说：是的，我有。"),
        ],
    },
    45: {
        "scope": "M2U2", "title": "Jobs",
        "focus": "职业和工作地点",
        "repeats": [
            "He is a firefighter.", "She is a nurse.",
            "My father is a teacher.", "The doctor works in a hospital.",
            "Mr Li is a bus driver.", "Firefighters can put out a fire.",
        ],
        "qa": [
            ("What does Jill's mother do?", "She is a nurse.", "用英语说：她是一名护士。"),
            ("Is Mr Black a firefighter?", "Yes, he is.", "用英语说：是的，他是。"),
        ],
    },
    46: {
        "scope": "M2U3", "title": "Friends",
        "focus": "朋友、衣着、外貌和爱好",
        "repeats": [
            "I have a new friend.", "Her name is Alice.",
            "She has long hair.", "She has a yellow dress.",
            "She can draw well.", "She likes reading.",
        ],
        "qa": [
            ("What does Alice have?", "She has a yellow dress.", "用英语说：她有一条黄色连衣裙。"),
            ("What does she like doing?", "She likes reading.", "用英语说：她喜欢阅读。"),
        ],
    },
    47: {
        "scope": "M3U1", "title": "In our school",
        "focus": "学校地点和there be",
        "repeats": [
            "There is a library in our school.", "There are twelve classrooms.",
            "The playground is behind the hall.", "The office is on the first floor.",
            "We can read in the library.", "We can run in the playground.",
        ],
        "qa": [
            ("Is there a library?", "Yes, there is.", "用英语说：是的，有。"),
            ("Where is the playground?", "It is behind the hall.", "用英语说：它在礼堂后面。"),
        ],
    },
    48: {
        "scope": "M3U2", "title": "Around my home",
        "focus": "社区地点和方位",
        "repeats": [
            "There is a supermarket near my home.", "The post office is next to the bakery.",
            "The restaurant is between two shops.", "Nanjing Road is very busy.",
            "Can you show me the way?", "It is my pleasure.",
        ],
        "qa": [
            ("Where is the post office?", "It is next to the bakery.", "用英语说：它在面包店旁边。"),
            ("Is there a restaurant?", "Yes, there is.", "用英语说：是的，有。"),
        ],
    },
    49: {
        "scope": "M1-M2", "title": "People and families",
        "focus": "人物、家庭、职业、感受和能力",
        "repeats": [
            "Her name is Jill.", "She is eleven years old.",
            "She can draw well.", "She likes reading.",
            "Her mother is a nurse.", "She has a cousin.",
        ],
        "qa": [
            ("What can Jill do?", "She can draw well.", "用英语说：她画画画得很好。"),
            ("What does her mother do?", "She is a nurse.", "用英语说：她是一名护士。"),
        ],
    },
    50: {
        "scope": "M1-M3U2", "title": "Full review",
        "focus": "人物、能力、学校和社区综合表达",
        "repeats": [
            "Alice is my classmate.", "She can swim well.",
            "Her father is a teacher.", "There is a library in her school.",
            "The playground is behind the hall.", "A supermarket is next to her home.",
        ],
        "qa": [
            ("Where is the playground?", "It is behind the hall.", "用英语说：它在礼堂后面。"),
            ("Is there a supermarket near her home?", "Yes, there is.", "用英语说：是的，有。"),
        ],
    },
}


def write_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2)
        fh.write("\n")


def main():
    for number in range(41, 51):
        listening = build_listening(number, LISTENING[number])
        speaking = build_speaking(number, SPEAKING[number])
        write_json(os.path.join(LISTENING_DIR, listening["course_id"] + ".json"), listening)
        write_json(os.path.join(SPEAKING_DIR, speaking["course_id"] + ".json"), speaking)
        print("built %s / %s" % (listening["course_id"], speaking["course_id"]))


if __name__ == "__main__":
    main()
