import os
import shutil
import uuid
import tempfile
from flask import session

EMAIL_CONTENT_TXT_FILE = 'email_content.txt'

def determine_flask_session_id():
    session_id = session.get('session_id')
    if not session_id:
        session_id = str(uuid.uuid4())
        session['session_id'] = session_id
    return session_id

def determine_output_folder() -> str:
    if os.getenv("APP_IN_DOCKER") == "Yes":
        print("DOCKER EXECUTION DETECTED")
        session_id = determine_flask_session_id()
        output_dir = os.path.join(tempfile.gettempdir(), session_id)
        print(f"Txt files directory for session id {session_id} set as: {output_dir}")
    else:
        output_dir = os.path.abspath(os.path.join(os.getcwd(), 'txt_files'))
        print(f"Txt files directory set as: {output_dir}")

    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    os.makedirs(output_dir)
    return output_dir