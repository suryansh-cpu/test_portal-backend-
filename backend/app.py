

# from fastapi import FastAPI, HTTPException, Body
# from pydantic import BaseModel
# from motor.motor_asyncio import AsyncIOMotorClient
# from dotenv import load_dotenv
# from typing import List
# from bson import ObjectId
# from datetime import datetime, timezone
# import random
# import uuid
# import os

# # Load environment variables
# load_dotenv()
# MONGO_URI = "mongodb://localhost:27017"
# DB_NAME = "test_portal"

# # Initialize app
# app = FastAPI(title="Test Portal Backend")

# # MongoDB connection
# client = AsyncIOMotorClient(MONGO_URI)
# db = client[DB_NAME]
# tests_collection = db["tests"]
# questions_collection = db["questions"]

# # ------------------------- Models -------------------------

# class Item(BaseModel):
#     name: str
#     value: str

# # ------------------------- Routes -------------------------

# @app.get("/")
# async def root():
#     return {"message": "Backend running successfully!"}

# # ----------------------------------------------------------
# # ✅ ADD QUESTION
# # ----------------------------------------------------------
# @app.post("/add_question")
# async def add_question(data: dict = Body(...)):
#     """
#     Add a question to MongoDB.
#     Supported types: mcq, multi_mcq, text, numeric, code
#     Example:
#     {
#         "question": "Which are programming languages?",
#         "type": "multi_mcq",
#         "options": ["Python", "HTML", "C++", "CSS"],
#         "answer": ["Python", "C++"]
#     }
#     """
#     q_type = data.get("type")

#     if q_type not in ["mcq", "multi_mcq", "text", "numeric", "code"]:
#         raise HTTPException(status_code=400, detail="Invalid question type")

#     if "question" not in data:
#         raise HTTPException(status_code=400, detail="Missing field: question")

#     if q_type in ["mcq", "multi_mcq"]:
#         options = data.get("options")
#         if not options or not isinstance(options, list):
#             raise HTTPException(status_code=400, detail="Options must be a list")

#         correct = data.get("answer")
#         if not correct:
#             raise HTTPException(status_code=400, detail="Missing 'answer'")

#         # Normalize
#         if q_type == "mcq" and isinstance(correct, list):
#             correct = correct[0]
#         if q_type == "multi_mcq" and isinstance(correct, str):
#             correct = [correct]

#         data["options"] = options
#         data["answer"] = correct

#     elif q_type == "numeric":
#         if "answer" not in data:
#             raise HTTPException(status_code=400, detail="Numeric question requires 'answer'")

#     await questions_collection.insert_one(data)
#     return {"message": f"{q_type} question added successfully"}

# # ----------------------------------------------------------
# # ✅ GET QUESTIONS
# # ----------------------------------------------------------
# @app.get("/get_questions")
# async def get_questions():
#     cursor = questions_collection.find({}, {"_id": 0})
#     questions = [q async for q in cursor]
#     return {"questions": questions}

# # ----------------------------------------------------------
# # ✅ START TEST
# # ----------------------------------------------------------
# @app.post("/start_test/{user_id}")
# async def start_test(user_id: str, num_questions: int = None):
#     """
#     Starts a test session.
#     """
#     cursor = questions_collection.find({}, {"_id": 1, "question": 1, "type": 1, "options": 1})
#     all_questions = []
#     async for q in cursor:
#         item = {
#             "qid": str(q["_id"]),
#             "question": q["question"],
#             "type": q["type"],
#             "options": q.get("options", [])
#         }
#         all_questions.append(item)

#     if not all_questions:
#         raise HTTPException(status_code=404, detail="No questions found")

#     if num_questions and num_questions < len(all_questions):
#         selected = random.sample(all_questions, num_questions)
#     else:
#         selected = all_questions.copy()

#     random.shuffle(selected)
#     test_id = str(uuid.uuid4())

#     test_doc = {
#         "test_id": test_id,
#         "user_id": user_id,
#         "questions": selected,
#         "started_at": datetime.now(tz=timezone.utc).isoformat(),
#         "ended_at": None,
#         "score": None,
#         "completed": False
#     }
#     await tests_collection.insert_one(test_doc)
#     return {"test_id": test_id, "questions": selected}

# # ----------------------------------------------------------
# # ✅ END TEST (Evaluate + Finalize)
# # ----------------------------------------------------------
# @app.post("/end_test/{test_id}")
# async def end_test(test_id: str, data: dict = Body(...)):
#     """
#     Ends a test, evaluates all answers, and finalizes the result.

#     Example request body:
#     {
#         "answers": [
#             {"qid": "<id>", "user_answer": "4"},
#             {"qid": "<id>", "user_answer": ["Python", "C++"]}
#         ]
#     }
#     """
#     test_doc = await tests_collection.find_one({"test_id": test_id})
#     if not test_doc:
#         raise HTTPException(status_code=404, detail="Test not found")

#     if test_doc.get("completed"):
#         raise HTTPException(status_code=400, detail="Test already completed")

#     answers = data.get("answers")
#     if not answers or not isinstance(answers, list):
#         raise HTTPException(status_code=400, detail="Answers must be provided as a list")

#     score = 0
#     total = 0
#     results = []

#     # Create a lookup for faster access
#     answer_map = {a["qid"]: a["user_answer"] for a in answers if "qid" in a}

#     for q in test_doc["questions"]:
#         qid = q["qid"]
#         user_ans = answer_map.get(qid)
#         question_doc = await questions_collection.find_one({"_id": ObjectId(qid)})

#         if not question_doc:
#             continue

#         q_type = question_doc.get("type")
#         correct_ans = question_doc.get("answer")
#         evaluated = False
#         correct = False

#         if q_type in ["mcq", "multi_mcq", "numeric"]:
#             total += 1
#             evaluated = True

#             if q_type == "mcq":
#                 if str(user_ans).strip().lower() == str(correct_ans).strip().lower():
#                     correct = True
#             elif q_type == "multi_mcq":
#                 if isinstance(user_ans, list) and set(map(str, user_ans)) == set(map(str, correct_ans)):
#                     correct = True
#             elif q_type == "numeric":
#                 try:
#                     if float(user_ans) == float(correct_ans):
#                         correct = True
#                 except Exception:
#                     correct = False

#             if correct:
#                 score += 1

#         results.append({
#             "question": question_doc["question"],
#             "user_answer": user_ans,
#             "correct_answer": correct_ans if evaluated else None,
#             "result": "correct" if correct else ("incorrect" if evaluated else "not evaluated")
#         })

#     # Finalize test
#     await tests_collection.update_one(
#         {"test_id": test_id},
#         {"$set": {
#             "completed": True,
#             "ended_at": datetime.utcnow().isoformat(),
#             "score": score,
#             "total": total,
#             "results": results
#         }}
#     )

#     return {
#         "message": "Test completed and evaluated",
#         "test_id": test_id,
#         "score": score,
#         "total": total,
#         "results": results
#     }




# 
# 
#               CODE ---- 2       
# 
# 



# from fastapi import FastAPI, HTTPException
# from pydantic import BaseModel
# from bson import ObjectId
# from pymongo import MongoClient
# import uuid
# import random
# from datetime import datetime

# # -------------------------------
# # MongoDB Connection
# # -------------------------------
# client = MongoClient("mongodb://localhost:27017/")
# db = client["test_portal"]
# questions_collection = db["questions"]
# results_collection = db["results"]
# tests_collection = db["tests"]

# # -------------------------------
# # FastAPI App
# # -------------------------------
# app = FastAPI()
# active_tests = {}  # Stores ongoing tests in memory

# # -------------------------------
# # Pydantic Models
# # -------------------------------
# class AnswerRequest(BaseModel):
#     test_id: str
#     qid: str
#     answer: str | list

# # -------------------------------
# # Start Test Endpoint
# # -------------------------------

# @app.post("/start_test/{user_id}")
# def start_test(user_id: str):
#     # Get all questions from MongoDB
#     all_questions = list(questions_collection.find({}))
#     if not all_questions:
#         raise HTTPException(status_code=404, detail="No questions found")

#     # Randomly pick 20
#     random.shuffle(all_questions)
#     selected_questions = all_questions[:20]

#     # Convert ObjectIds to strings and remove correct answers
#     safe_questions = []
#     for q in selected_questions:
#         q_copy = q.copy()
#         q_copy["_id"] = str(q_copy["_id"])
#         q_copy.pop("correct_answer", None)
#         safe_questions.append(q_copy)

#     # Store test info
#     test_id = str(uuid.uuid4())
#     started_at = datetime.now()

#     tests_collection.insert_one({
#         "test_id": test_id,
#         "user_id": user_id,
#         "questions": safe_questions,   # <--- use safe version
#         "started_at": started_at,
#         "answers": {},
#         "completed": False
#     })

#     # Return first question (without correct_answer)
#     first_question = safe_questions[0]

#     return {
#         "test_id": test_id,
#         "current_index": 0,
#         "total_questions": len(safe_questions),
#         "question": first_question,
#         "started_at": started_at.isoformat()
#     }

# # @app.post("/start_test/{username}")
# # def start_test(username: str):
# #     # Fetch only mcq, multi_mcq, numeric questions
# #     all_questions = list(questions_collection.find(
# #         {"type": {"$in": ["mcq", "multi_mcq", "numeric"]}},
# #         {"answer": 0}
# #     ))

# #     if not all_questions:
# #         raise HTTPException(status_code=404, detail="No questions found in database.")

# #     # Shuffle
# #     random.shuffle(all_questions)

# #     # Create test_id
# #     test_id = str(uuid.uuid4())
# #     order = [str(q["_id"]) for q in all_questions]

# #     # Store in active tests
# #     active_tests[test_id] = {
# #         "username": username,
# #         "order": order,
# #         "answers": {},
# #         "started_at": datetime.utcnow(),
# #     }

# #     # Return first question
# #     first_question = all_questions[0]
# #     first_question["_id"] = str(first_question["_id"])

# #     return {
# #         "test_id": test_id,
# #         "current_index": 0,
# #         "total_questions": len(order),
# #         "question": first_question,
# #         "started_at": active_tests[test_id]["started_at"]
# #     }

# # -------------------------------
# # Get Question by Index
# # -------------------------------
# @app.get("/get_question/{test_id}/{index}")
# def get_question(test_id: str, index: int):
#     if test_id not in active_tests:
#         raise HTTPException(status_code=404, detail="Test not found")

#     test_data = active_tests[test_id]
#     order = test_data["order"]

#     if index < 0 or index >= len(order):
#         raise HTTPException(status_code=400, detail="Invalid index")

#     qid = order[index]
#     question = questions_collection.find_one({"_id": ObjectId(qid)}, {"answer": 0})
#     if not question:
#         raise HTTPException(status_code=404, detail="Question not found")

#     question["_id"] = str(question["_id"])
#     return {
#         "test_id": test_id,
#         "index": index,
#         "total_questions": len(order),
#         "question": question
#     }

# # -------------------------------
# # Save or Update Answer
# # -------------------------------
# @app.post("/save_answer")
# def save_answer(data: AnswerRequest):
#     if data.test_id not in active_tests:
#         raise HTTPException(status_code=404, detail="Test not found")

#     test_data = active_tests[data.test_id]
#     qid = data.qid

#     # Save or update answer
#     test_data["answers"][qid] = data.answer

#     return {"status": "saved", "qid": qid, "answer": data.answer}

# # -------------------------------
# # End Test
# # -------------------------------
# @app.post("/end_test/{test_id}")
# def end_test(test_id: str):
#     if test_id not in active_tests:
#         raise HTTPException(status_code=404, detail="Test not found")

#     test_data = active_tests.pop(test_id)
#     test_data["ended_at"] = datetime.utcnow()

#     # Save to MongoDB results collection
#     results_collection.insert_one({
#         "test_id": test_id,
#         "username": test_data["username"],
#         "answers": test_data["answers"],
#         "started_at": test_data["started_at"],
#         "ended_at": test_data["ended_at"],
#     })

#     return {"status": "completed", "test_id": test_id, "total_answered": len(test_data["answers"])}

# # -------------------------------
# # Root Route
# # -------------------------------
# @app.get("/")
# def root():
#     return {"message": "C++ Test API running successfully!"}




# 
# 
#           CODE ---- 3
# 
# 



from fastapi import FastAPI, HTTPException, Body
from pydantic import BaseModel
from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime
import random
import uuid

# -------------------------------
# MongoDB Connection
# -------------------------------
client = MongoClient("mongodb://localhost:27017/")
db = client["test_portal"]
questions_collection = db["questions"]
tests_collection = db["tests"]
results_collection = db["results"]

# -------------------------------
# FastAPI App
# -------------------------------
app = FastAPI(title="C++ Test API")

# -------------------------------
# Pydantic Models
# -------------------------------
class AnswerRequest(BaseModel):
    test_id: str
    qid: str
    answer: str | list

# -------------------------------
# Active Test Memory
# -------------------------------
active_tests = {}

# -------------------------------
# Start Test
# -------------------------------
@app.post("/start_test/{username}")
def start_test(username: str):
    all_questions = list(questions_collection.find(
        {"type": {"$in": ["mcq", "multi_mcq", "numeric"]}}
    ))

    if not all_questions:
        raise HTTPException(status_code=404, detail="No questions found")

    random.shuffle(all_questions)
    selected_questions = all_questions[:20]

    # remove correct answers before sending
    for q in selected_questions:
        q["_id"] = str(q["_id"])
        q.pop("correct_answer", None)

    test_id = str(uuid.uuid4())
    order = [q["_id"] for q in selected_questions]
    started_at = datetime.utcnow()

    # save in memory
    active_tests[test_id] = {
        "username": username,
        "order": order,
        "answers": {},
        "started_at": started_at,
    }

    # save in DB
    tests_collection.insert_one({
        "test_id": test_id,
        "username": username,
        "questions": selected_questions,
        "started_at": started_at,
        "completed": False
    })

    return {
        "test_id": test_id,
        "current_index": 0,
        "total_questions": len(order),
        "question": selected_questions[0],
        "started_at": started_at.isoformat()
    }

# -------------------------------
# Get Question by Index
# -------------------------------
@app.get("/get_question/{test_id}/{index}")
def get_question(test_id: str, index: int):
    if test_id not in active_tests:
        raise HTTPException(status_code=404, detail="Test not found")

    test_data = active_tests[test_id]
    order = test_data["order"]

    if index < 0 or index >= len(order):
        raise HTTPException(status_code=400, detail="Invalid index")

    qid = order[index]
    question = questions_collection.find_one({"_id": ObjectId(qid)}, {"correct_answer": 0})
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    question["_id"] = str(question["_id"])
    return {
        "test_id": test_id,
        "index": index,
        "total_questions": len(order),
        "question": question
    }

# -------------------------------
# Submit Answer
# -------------------------------
@app.post("/submit_answer")
def submit_answer(data: AnswerRequest):
    if data.test_id not in active_tests:
        raise HTTPException(status_code=404, detail="Test not found")

    test_data = active_tests[data.test_id]
    test_data["answers"][data.qid] = data.answer

    return {"status": "saved", "qid": data.qid, "answer": data.answer}

# -------------------------------
# End Test (Evaluate)
# -------------------------------
@app.post("/end_test/{test_id}")
def end_test(test_id: str):
    if test_id not in active_tests:
        raise HTTPException(status_code=404, detail="Test not found")

    test_data = active_tests.pop(test_id)
    answers = test_data["answers"]
    username = test_data["username"]
    order = test_data["order"]

    score = 0
    total = len(order)
    results = []

    for qid in order:
        question = questions_collection.find_one({"_id": ObjectId(qid)})
        if not question:
            continue

        user_ans = answers.get(qid)
        correct_ans = question.get("correct_answer")
        q_type = question.get("type")
        correct = False

        if q_type == "mcq":
            correct = str(user_ans).strip().lower() == str(correct_ans).strip().lower()
        elif q_type == "multi_mcq":
            correct = isinstance(user_ans, list) and set(map(str, user_ans)) == set(map(str, correct_ans))
        elif q_type == "numeric":
            try:
                correct = float(user_ans) == float(correct_ans)
            except Exception:
                correct = False

        if correct:
            score += 1

        results.append({
            "question": question["question"],
            "user_answer": user_ans,
            "correct_answer": correct_ans,
            "result": "correct" if correct else "incorrect"
        })

    ended_at = datetime.utcnow()
    results_collection.insert_one({
        "test_id": test_id,
        "username": username,
        "score": score,
        "total": total,
        "results": results,
        "started_at": test_data["started_at"],
        "ended_at": ended_at
    })

    return {
        "status": "completed",
        "test_id": test_id,
        "username": username,
        "score": score,
        "total": total,
        "accuracy": f"{(score / total) * 100:.2f}%",
        "results_saved": True
    }

# -------------------------------
# Root Route
# -------------------------------
@app.get("/")
def root():
    return {"message": "C++ Test API running successfully!"}
