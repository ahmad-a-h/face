import face_recognition
import numpy as np
from PIL import Image
import base64
from PIL import Image
from io import BytesIO
import tempfile
from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
import requests
import json

app = Flask(__name__)
CORS(app)
@app.route('/compare', methods=['POST'])
def compare_faces():
    data = request.get_json()
    image1_path = data['image1_base64']
    arrStudent = data['arrStudent']
    sessionID = data['sessionId']
    # Load the images
    max_confidence = 0
    best_match = None
    match_found = False  # Flag variable

    for face_object in arrStudent:
        image1 = decode_base64_to_image(image1_path)
        image_path1 = save_image_to_temp_file(image1)
        print(face_object)
        image2 = decode_base64_to_image(face_object['face']['faceEncoding'])
        image_path2 = save_image_to_temp_file(image2)

        image1 = face_recognition.load_image_file(image_path1)
        image2 = face_recognition.load_image_file(image_path2)
        # Encode the faces in the images

        encoding1 = face_recognition.face_encodings(image1)[0]
        encoding2 = face_recognition.face_encodings(image2)[0]

        if len(encoding1) == 0:
            return jsonify({'error': 'No face found in image 1.'}), 400

        if len(encoding2) == 0:
            return jsonify({'error': 'No face found in image 2.'}), 400

        # Compare the face encodings
        results = face_recognition.compare_faces([encoding1], encoding2)
        face_distance = face_recognition.face_distance([encoding1], encoding2)
        confidence = (1 - face_distance) * 100

        if confidence > max_confidence:
            max_confidence = confidence
            best_match = face_object

        if max_confidence > 60.0:
            print("Match found!")
            match_found = True
            print(f"Student ID: {face_object['id']}")
            url = 'https://seniorbackend.azurewebsites.net/createAttendance'
            params = {
                "sessionid": data['sessionId'],
                "studentId": face_object['id'],
                "timeAttended":str(datetime.now().time()),
                "matchPerc":float(max_confidence)

            }
            result = public_post(url, params)
            

            # Return the one that has the greatest confidence
            return jsonify({'match': True, 'student': face_object, 'conf': float(max_confidence)}), 200

    if not match_found:
        return jsonify({"message": "No match found"}), 400


    # Return the results
    # return

def decode_base64_to_image(base64_string):
    # Remove the data URI scheme prefix if present
    if base64_string.startswith("data:image"):
        base64_string = base64_string.split(",", 1)[1]

    # Decode the base64 string into bytes
    image_bytes = base64.b64decode(base64_string)

    # Create a BytesIO object to read the image bytes
    image_buffer = BytesIO(image_bytes)

    # Open the image using PIL
    image = Image.open(image_buffer)

    return image

def save_image_to_temp_file(image):
    temp_file = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False)
    temp_file_path = temp_file.name
    image.save(temp_file_path)
    temp_file.close()
    return temp_file_path
    
def public_post(url, params):
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Access-Control-Allow-Origin": "*"
    }
    json_data = json.dumps(params)
    response = requests.post(url, json=params, headers=headers)
    return response


if __name__ == '__main__':
    app.run()
