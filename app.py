from flask import Flask,jsonify,request,send_from_directory
from flask_cors import CORS
from openai import OpenAI
import uuid
import os
import json
import re
from dotenv import load_dotenv
from werkzeug.utils import secure_filename


app=Flask(__name__)
CORS(app) 


# load .env file
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


client = OpenAI(api_key=OPENAI_API_KEY)
Audio_folder = "./uploads"
os.makedirs(Audio_folder, exist_ok=True)


@app.route('/chat',methods=["POST"])
def replay():

    data=request.json

    message = data.get("message")
    data = data.get("ID")

    goals = data.get("Goals", "")
    style = data.get("style", "")
    type_of_model = data.get("type", "")

# Build dynamic system prompt
    system_prompt = f"""
You are an AI model called AImate.
- Model Type: {type_of_model}
- Style: {style}
- Goals: {goals}

Stay consistent with this role while chatting. 
Be friendly, supportive, and context-aware.
Try often to use remeber user it's goal
"""

    response = client.chat.completions.create(
    model="gpt-4.1-mini",
    messages=[
        {"role": "system", "content": system_prompt.strip()},
        {"role": "user", "content": message}
    ],
    max_tokens=200
)

    ai_message = response.choices[0].message.content

    return jsonify({
        "id":1234567,
        "message":ai_message
    })



@app.route('/live',methods=["POST"])
def live_chat():
    data=request.json
    URL=data.get("URl")
    # role=data.get("Role")
    # name=data.get("name")
    # type_AI=data.get("type")
    role="Designer"
    name="pikachu"
    type_AI="introvert"

    with open("audio.wav",'rb') as audio_file:
        transcript=client.audio.transcriptions.create(
            model="gpt-4o-mini-transcribe",
            file=audio_file
        )
    text=transcript.text

    response=client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role":"system","content":f"Your role is {role} and act like {type_AI} and your name is {name}"},
            {"role":"user","content":text}
        ],
        max_tokens=300
    )    
    answer=response.choices[0].message.content

    

    final= client.audio.speech.with_raw_response.create(
        model="gpt-4o-mini-tts",
        voice='ash',
        input=answer
    ) 

    with open("answer.mp3", "wb") as f:
        f.write(final.content)

    return jsonify({"message":"Done "})    



@app.route('/upload', methods=["POST"])
def upload_voice():
    if "file" not in request.files:
        return jsonify({'error': "No file provided"}), 400

    try:
        # === Save Uploaded File ===
        file = request.files["file"]
        filename = f"{uuid.uuid4()}.webm"
        safe_path = os.path.join(Audio_folder, secure_filename(filename))
        file.save(safe_path)

        # === Personality ===
        personality = request.form.get("personality", "Steve Jobs")
        role = "businessman"
        name = personality
        type_ai = f"Acts like {personality} and personality similar to him"
        language = "urdu"

        # === Transcribe Audio ===
        with open(safe_path, 'rb') as audio_file:
            transcript = client.audio.transcriptions.create(
                model="gpt-4o-mini-transcribe",
                file=audio_file
            )
        user_input = transcript.text

        if not user_input.strip():
            return jsonify({'error': "Audio transcription failed or empty."}), 400

        # === Get AI Reply ===
        system_prompt = (
            f"Your role is {role}. Act like {type_ai}. "
            f"Your name is {name}. Always respond in {language}."
        )

        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input}
            ],
            max_tokens=300
        )

        answer = response.choices[0].message.content

        # === Generate Speech ===
        speech_response = client.audio.speech.with_raw_response.create(
            model="gpt-4o-mini-tts",
            voice="ash",
            input=answer
        )

        audio_output_name = f"{uuid.uuid4()}.mp3"
        audio_output_path = os.path.join(Audio_folder, secure_filename(audio_output_name))
        with open(audio_output_path, "wb") as out_f:
            out_f.write(speech_response.content)
            

        print("Saved audio file to:", audio_output_path)
        print("Size:", os.path.getsize(audio_output_path), "bytes")
            
        if not os.path.exists(audio_output_path):
            print("❌ File was not saved!")

        return jsonify({
            "message": answer,
            "filename": audio_output_name
        }), 200

    except Exception as e:
        return jsonify({
            "error": str(e),
            "stage": "processing"
        }), 500


@app.route("/uploads/<filename>")
def get_file(filename):
    return send_from_directory(Audio_folder, filename)


@app.route("/test",methods=["POST"])
def create_TEST():
   try:
        data=request.json

        sallabus=data["sallabus"]
        chapter=data["chapter"]
        topic=data["topic"]
        subTopic=data["subtopic"]

        response=client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": """
You are an AI tutor that generates multiple-choice questions (MCQs).
Your job is to create exactly 5 questions for students.
Each question must have:
- A clear question statement.
- 4 options labeled A, B, C, D.
- The correct answer.
- A difficulty level: Easy, Medium, or Hard.
Return the output in JSON format.
"""},
            {"role":"user","content":f'''
Create a 5-question multiple choice test for the sallabus: "{sallabus}" 
and chapter: "{chapter}".
with the topic:{topic} and the subtopic :{subTopic}
Make sure the difficulty levels are mixed (at least 1 Easy, 2 Medium, 2 Hard).

'''}
        ]
    )

        raw_answer = response.choices[0].message.content
        cleaned = re.sub(r"```json|```", "", raw_answer).strip()

        # Parse into Python object
        parsed_json = json.loads(cleaned)


        return jsonify({
        "status":"secessfull",
        "answer":parsed_json
    })

   except Exception as e:
       return jsonify({
           "status":"ERROR",
           "ERROR":str(e)
       })


@app.route("/community",methods=["POST"])
def community():
    try:
        data=request.json
        text=data.get("message")

        system_prompt='''
I will give you a short description of a community or event type.
Based on that description, generate a JSON schema of fields that should be collected for it.
Each field should include:

"name": the field name

"type": data type (string, number, date, boolean, etc.)

"required": true/false

Example input:
"A Model United Nations conference for students to participate in debates and discussions"

Example output:

{
  "communityType": "MUN",
  "fields": [
    { "name": "Name", "type": "string", "required": true },
    { "name": "Description", "type": "string", "required": true },
    { "name": "Venue", "type": "string", "required": true },
    { "name": "Date", "type": "date", "required": true },
    { "name": "Price", "type": "number", "required": false },
    { "name": "Organizer", "type": "string", "required": true }
  ]
}


Please always output only JSON, with "communityType" guessed from the description, and "fields" generated accordingly.
Also always remeber to add instagram account in every condition 
'''

        response=client.chat.completions.create(
        model='gpt-4o-mini',
        messages=[
            {"role":"system","content":system_prompt},
            {"role":"user","content":text}
        ],
        max_tokens=600
    )
        

        raw_answer = response.choices[0].message.content
        cleaned = re.sub(r"```json|```", "", raw_answer)
        parsed = json.loads(cleaned)
        return jsonify({
        "status":"Succesful",
        "message":parsed
    })

    except Exception as e:
        return jsonify({
            "status":"Failed",
            "message":str(e)
        })


@app.route("/study",methods=["POST"])
def study():
    data = request.get_json()
    question = data.get("question")

    try:
        system_prompt = f"""
You are an intelligent AI study assistant. Explain the topic in a simple and helpful way so a student can understand. Use examples when needed.
"""

        response = client.chat.completions.create(
    model="gpt-4.1-mini",
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": question}
    ],
    max_tokens=200
)
    
        ai_message = response.choices[0].message.content

        return jsonify({
        "message":ai_message,
        "Status":"PASS"
    })

    except Exception as e:
        return jsonify({
            "message":str(e),
            "status":"FAIL:"
        })




if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
