from flask import Flask,jsonify,request,send_from_directory
from flask_cors import CORS
from openai import OpenAI
import uuid
import os
import json
import re
from dotenv import load_dotenv

app=Flask(__name__)
CORS(app) 


# load .env file
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


client = OpenAI(api_key=OPENAI_API_KEY)
Audio_folder="./uploads"

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


@app.route('/upload',methods=["POST"])
def upload_voice():
    if "file" not in request.files:
        return jsonify ({'Error':"There is not any file"}),400
    
    try:
        files = request.files['file']
        file_name=f'{uuid.uuid4()}.webm'
        file_path=os.path.join(Audio_folder,file_name)
        files.save(file_path)

        role="bussinesman"
        name="Steve jobs"
        type_AI="Acts like steve jobs and personality similar to him "
        languge="urdu"
        with open(file_path,'rb') as audio_file:
            transcript=client.audio.transcriptions.create(
                model="gpt-4o-mini-transcribe",
                file=audio_file
            )
        text=transcript.text

        response=client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role":"system","content":f"Your role is {role} and act like {type_AI} and your name is {name} and give answer in {languge} always"},
            {"role":"user","content":text}
        ],
        max_tokens=300
    )    
        answer=response.choices[0].message.content

    

        final= client.audio.speech.with_raw_response.create(
        model="gpt-4o-mini-tts",
        voice='ash',
        input=answer) 

       
        output_name = f"{uuid.uuid4()}.mp3"
        output_path = os.path.join(Audio_folder, output_name)
        with open(output_path, "wb") as f:
            f.write(final.content)

        return jsonify({
            "message":answer,
            "filename":output_name
        })
    
    except Exception as e :
        return jsonify({
            "error":str(e),
            "stage":"stage_2"

            })


@app.route("/uploads/<filename>")
def get_file(filename):
    return send_from_directory(Audio_folder,filename)

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



# if __name__ == "__main__":
#     app.run(host="0.0.0.0", port=5000)


if __name__=="__main__":
    app.run(debug=True)