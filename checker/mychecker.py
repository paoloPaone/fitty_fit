#!/usr/bin/env python3

from uuid import uuid4
from ctf_gameserver import checkerlib
import requests
from pikepdf import Pdf
from fpdf import FPDF
from requests import Session
import logging
import time
import base64
import struct
import hashlib
import random
import string
import hmac
import io

PORT = 5001

"""
    Checker TODO:
    * Transfer
    * check if you can read damaged
    * check if you can see generated
    * see if damaged is stored
"""
def totp(key, interval=60):
    now=time.time()
    try:
        key = key.encode()
        counter = struct.pack('>Q', int(now / interval))
        mac = hmac.new(key, counter, hashlib.sha256).digest()
        password = base64.b32encode(mac).decode().replace("=", "")
    except Exception as e:
        print(e)
        password = None
    return password


def log_error_and_quit(res, msg):
    logging.error(f"URL: {res.request.method} {res.request.url} - {msg}")
    return None

class MyChecker(checkerlib.BaseChecker):

    def __init__(self, ip, team):
        checkerlib.BaseChecker.__init__(self, ip, team)
        self._baseurl = f'http://{self.ip}:{PORT}/'
        logging.info(f"URL: {self._baseurl}")

    def place_flag(self, tick):
        self.session = Session()
        if not self._check_index():
            return checkerlib.CheckResult.DOWN

        # Create PDF
        flag = checkerlib.get_flag(tick)     
        print(flag)
        pdf = self._write_pdf(flag)

        # Register
        uid = str(uuid4())
        name = "MrFlag_" + uid
        key = self._register_user(name)
        if not key:
            return checkerlib.CheckResult.FAULTY

        if self._login_user(name, key) == False:
            return checkerlib.CheckResult.FAULTY

        # Upload
        filename = "FlagNFT_" + uid + ".pdf"        
        if not self._upload_file(filename, pdf):
            return checkerlib.CheckResult.FAULTY
            
        data = {
            "step": "generate",
            "filename": filename,
            "creator": name,
            "description": "A great hacking exercise!",
            "part": "All parts of the brain",
            "score": "1337",
            "level": "medium"
        }
        if not self._generate_file(data):
            return checkerlib.CheckResult.FAULTY

        checkerlib.store_state("flag_" + str(tick), {"name": name, "key": key})
        checkerlib.set_flagid(name)

        return checkerlib.CheckResult.OK

    def check_service(self): 
        self.session = Session()
        if not self._check_index():
            return checkerlib.CheckResult.DOWN

        # Test register
        name = "User" + "".join([random.choice(string.ascii_letters) for _ in range(12)])
        key = self._register_user(name)
        if not key:
            return checkerlib.CheckResult.FAULTY

        if self._login_user(name, key) == False:
            return checkerlib.CheckResult.FAULTY
        
        # Create PDF
        pdf_content =  "".join([random.choice(string.ascii_letters) for _ in range(12)])
        pdf = self._write_pdf(pdf_content)

        # Check Upload
        filename = str(uuid4()) + ".pdf"        
        if not self._upload_file(filename, pdf):
            return checkerlib.CheckResult.FAULTY

        data = {
            "step": "generate",
            "filename": filename,
            "creator": name,
            "description": "".join([random.choice(string.ascii_letters) for _ in range(12)]),
            "part": "".join([random.choice(string.ascii_letters) for _ in range(12)]),
            "score": "10",
            "level": "easy"
        }
        if not self._generate_file(data):
            return checkerlib.CheckResult.FAULTY

        # Check if file exists
        res = self.session.get(f"{self._baseurl}/home")
        files = res.text.split('<iframe src="')
        if len(files) < 2:
            logging.error(f"Not enough files:\n {res.text}")
            return checkerlib.CheckResult.FAULTY

        contents = []
        for f in files[1:]:
            path = f.split('"></iframe>')[0] 
            if name not in path:
                logging.error(f"NFT path is not complete: {path}")
                return checkerlib.CheckResult.FAULTY

            res = self.session.get(f"{self._baseurl}" + path, stream=True)

            try:
                binary = io.BytesIO(res.content)
                pdf = Pdf.open(binary)
                content = self._read_pdf(pdf)
                contents.append(content)
            except Exception as e:
                logging.error(f"PikePDF fails: {e}")
                continue


        if pdf_content.encode() not in b"".join(contents):
            logging.error(f"PDF Content is not part of contents: {pdf_content} not in {contents}")
            return checkerlib.CheckResult.FAULTY

        # TODO Check transfer
        # TODO session should be an array with multiple sessions
        """
        user_2 = "User" + "".join([random.choice(string.ascii_letters) for _ in range(12)])
        key_2 = self._register_user(name)
        if not key_2:
            return checkerlib.CheckResult.FAULTY

        if self._login_user(name_2, key_2) == False:
            return checkerlib.CheckResult.FAULTY
        
        data = {"filename": filename, "receiver": user_2}
        res = session.post(self._baseurl + "transfer", data=data)
        """
        # TODO Check if meta values are true


        return checkerlib.CheckResult.OK

    def check_flag(self, tick):
        self.session = Session()
        if not self._check_index():
            return checkerlib.CheckResult.DOWN
        flag = checkerlib.get_flag(tick)

        creds = checkerlib.load_state("flag_" + str(tick))
        if not creds:
            return checkerlib.CheckResult.FLAG_NOT_FOUND
            
        name, key = creds["name"], creds["key"]
        logging.info(f"Login as {name} with {key}. His flag is {flag}")

        if self._login_user(name, key) == False:
            return checkerlib.CheckResult.FLAG_NOT_FOUND
        
        res = self.session.get(f"{self._baseurl}/home")
        files = res.text.split('<iframe src="')[1:]
        for f in files:
            path = f.split('"></iframe>')[0]            
            print(path)
            res = self.session.get(f"{self._baseurl}" + path, stream=True)

            try:
                binary = io.BytesIO(res.content)
                pdf = Pdf.open(binary)
                content = self._read_pdf(pdf)
            except Exception as e:
                logging.error(f"PikePDF fails: {e}")
                continue

            print(flag)
            # print(content)
            if flag.encode() in content:
                return checkerlib.CheckResult.OK
        
        return checkerlib.CheckResult.FLAG_NOT_FOUND



    def _check_index(self):
        res = requests.get(f"{self._baseurl}/")
        if res.status_code != 200:
            log_error_and_quit(res, f"Status Code is not 200: {res.text}")
            return False
        return True

    def _register_user(self, username):
        data = {"name": username}
        res = self.session.post(self._baseurl + "register", data=data)
        if res.status_code != 200:
            return log_error_and_quit(res, f"Status Code is not 200: {res.text}")
            
        try:
            key = res.text.split("This is your key: <b>")[1].split("</b>")[0]    
        except Exception as e:
            return log_error_and_quit(res, f"No key found: {res.text}")
        return key
    
    def _login_user(self, username, key):
        password = totp(key)
        data = {"name": username, "pass": password}
        res = self.session.post(self._baseurl + "login", data=data)

        if res.status_code == 200 and "home" in res.url:
            logging.info("Successfully logged in!")
        else:
            log_error_and_quit(res, f"Failed to login with credentials {username} {password}:\n{res.text}")
            return False
        return True
    
    def _upload_file(self, filename, pdf):
        data = {"step": "upload"}
        files = {"file": (filename, pdf)}
        res = self.session.post(
            self._baseurl + "generate",
            files=files,
            data=data
        )
        if "M.toast" in res.text:
            log_error_and_quit(res, f"Failed to upload file:\n{res.text}")
            return False
        return True

    
    def _generate_file(self, data):
        res = self.session.post(
            self._baseurl + "generate",
            data=data
        )
        if "succesfully" not in res.text:
            log_error_and_quit(res, f"Failed to generate file:\n{res.text}")
            return False
        return True

    def _write_pdf(self, text):
        pdf = FPDF('P', 'mm', 'A4')
          
        pdf.add_page()
        pdf.set_font('Arial', 'B', 18)
        pdf.cell(40, 5, text, 0, 1)
        return pdf.output('', 'S').encode('latin-1')

    def _read_pdf(self, pdf):
        content = pdf.pages[0].Contents
        return content.read_bytes()

if __name__ == '__main__':
    checkerlib.run_check(MyChecker)
