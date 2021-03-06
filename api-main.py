from flask import Flask, render_template, request, redirect, url_for, jsonify, make_response
from pymongo import MongoClient
import random
import smtplib
from email.message import EmailMessage
from datetime import date
from credentials import cred
import json
from flask_cors import CORS, cross_origin
import datetime as dt

#database setup



app = Flask(__name__)
cors = CORS(app)
app.secret_key = "1iu2ihoi!@#$%^&*fsdhjfb"
client = MongoClient("localhost", 27017)

db = client["elec-vote"]
session = db["session"]
citizens = db["citizens"]
onlineVotingCred = db["onlineVotingCred"]
elecPlaces = db["elecPlaces"]
vote = db["vote"]

def sessionTime():
    dateNow = str(dt.datetime.date(dt.datetime.now())).split("-")
    timeNow = str(dt.datetime.time(dt.datetime.now())).split(":")
    dateNow = [int(x) for x in dateNow]
    timeNow = [int(float(x)) for x in timeNow]
    print("Session time called")
    return [dateNow, timeNow]

#route for result
@app.route('/result')
@cross_origin()
def result():
    data = db.vote.find_one({"username" : "admin"})
    bjpVote = str(data["bjp"])
    congVote = str(data["cong"])
    senaVote = str(data["sena"])
    notaVote = str(data["nota"])
    print(bjpVote)
    resp = make_response(render_template("result.html"))
    resp.set_cookie('BJP', bjpVote, max_age=5)
    resp.set_cookie('Congress', congVote, max_age=5)
    resp.set_cookie('Shivsena', senaVote, max_age=5)
    resp.set_cookie('NOTA', notaVote, max_age=5)
    return resp



#online voting cred of users registration and accordingly message generation

def onlineVotingCredReg(to, password, name):
    if (db.onlineVotingCred.find_one({"username": to})):
        found = db.onlineVotingCred.find_one({"username": to})
        username = found["username"]
        password = found["password"]
        message = "Hey " + name + ",\n\nYou already generated your password for online voting. Credentials for the same are as follows :\nYour login id : " + to + "\nYour login password : " + password + "\n\n\n\nThank you!!"
        return message
    else:
        db.onlineVotingCred.insert_one({"username" : to, "password" : password, "vote" : 0})
        message = "Hey " + name + ",\n\nYour login id : " + to + "\nYour login password : " + password + "\n\n\n\nThank you!!"
        return message

#email generation according to the user credentials generation requirement

def emailGen(to, password, name="ECI Admin"):
    s = smtplib.SMTP('smtp.gmail.com', 587)
    s.starttls()
    s.login(cred.emailId, cred.emailPass)
    msg = EmailMessage()
    if (name=="ECI Admin"):
        message = "Hey " + name + ",\n\nYour login otp is " + password + "\n\n\n\nThank you!!"
    else:
        message = onlineVotingCredReg(to, password, name)
    msg.set_content(message)
    msg['Subject'] = 'Online Voting Credentials'
    msg['From'] = "test.proje.niks@gmail.com"
    msg['To'] = to
    s.send_message(msg)
    s.quit()

#email on voting success

def emailSuc(to, name):
    s = smtplib.SMTP('smtp.gmail.com', 587)
    s.starttls()
    s.login(cred.emailId, cred.emailPass)
    msg = EmailMessage()
    message ="Hey, " + name.title() + "," +  "\n\nThank you for using Online Voting Application.\n Your vote has been successfully casted \n\n Regards\n ECI"
    msg.set_content(message)
    msg['Subject'] = 'Thank You - Online Voting'
    msg['From'] = "test.proje.niks@gmail.com"
    msg['To'] = to
    s.send_message(msg)
    s.quit()


#password generation for particular user

def password():
    key = "!@#$&*1234567890qwertyuiopasd12345QWERTYUIOPASDFGHJKLZXCVBNM67890fghjklzxcvbnm1234567890!@#$&*"
    key = list(key)
    random.shuffle(key)
    password = key[0:8]
    password = "".join(password)
    return password

#token generation

def token():
    key = "!@#$&*1234567890qwer!@#$%^&*()XFGHJKIUTYFUGCHVHYU&^%$%EYRUT&^%&$E^RTSX$%*()**^&%^$%$O*(&T*FYUVJHKBNIJP(U)*(&IYVBIPU*&^%EDHCVHGU&^ESXCJVKBJHYtyuiopasd12345QWERTYUIOPASDFGHJKLZXCVBNM67890fghjklzxcvbnm1234567890!@#$&*"
    key = list(key)
    random.shuffle(key)
    token = key[0:32]
    token = "".join(token)
    return token

#age calculation of the user

def age(dbDate):
    dbDate = dbDate.split("-")
    dbDate = [int(x) for x in dbDate]
    today = str(date.today()).split("-")
    today = [int(x) for x in today]
    age = date(today[0], today[1], today[2]) - date(dbDate[0], dbDate[1], dbDate[2])
    age = age.days // 365
    return age


# route for voting

@app.route("/vote", methods=["GET", "POST"])
@cross_origin()
def vote():
    try :
        if (request.method == "POST"):
            print("Chal gaya")
            persis_id = request.json["persis_id"]
            vote = str(request.json["vote"])
            print(persis_id)
            print(vote)
            data = db.session.find_one({"persis_id": persis_id})
            username = data["username"]
            emailNameData = db.citizens.find_one({"email" : username })
            name = emailNameData["name"]
            db.onlineVotingCred.update_one({"username" : username}, {"$set" : { "vote" : 1}})
            db.vote.update_one({"username" : "admin"}, {"$inc" : { vote : 1 }})
            db.session.delete_many({"username": username})
            emailSuc(username, name)
            error = "\n Thank you for using Online Voting. Your vote got casted sucessfully."
            resp = make_response(render_template("logout.html", error = error))
            resp.set_cookie('persis_id', '', expires=0)
            return resp
        elif (request.method == "GET"):
            return "You are logged out, try logging in again"
    except KeyError or NameError or ValueError:
        print("Nahi chala")
        return "You are logged out, try logging in again"


#route to remove particular place from db (elecPlaces)

@app.route("/remElecPlace", methods=["POST", "GET"])
@cross_origin()
def remElecPlace():
    try:
        username = request.json['username']
        persis_id = request.json['persis_id']
        if (db.session.find_one({'persis_id': persis_id})):
            if request.method == "POST":
                place = request.json['place'].strip()
                if (db.elecPlaces.find_one({"placeName" : place})):
                    db.elecPlaces.delete_one({"placeName" : place})
                    return "Place sucessfully removed"
                else:
                    return "Such place does not exist in the database"
            else:
                return "Try logging in first"
    except KeyError:
        db.session.delete_many({"username":username})
        return "Try logging in first you refreshed the page or you left the page idle for more than 10 minutes"


#adding place to database related to ECI Admin

@app.route("/addElecPlace", methods=["GET", "POST"])
@cross_origin()
def addElecPlace():
    try:
        username = request.json['username']
        persis_id = request.json['persis_id']
        if(db.session.find_one({'persis_id' : persis_id})):
            if request.method == 'POST':
                place = request.json['place'].strip()
                if (len(place) == 0):
                    return "You cannot add empty places to the database"
                else:
                    if (db.elecPlaces.find_one({"placeName" : place})):
                        return "Place already exist"
                    else:
                        db.elecPlaces.insert_one({"placeName" : place})
                        return "Place Added Successfully"
        else:
            return "Try logging in first"
    except KeyError:
        db.session.delete_many({"username":username})
        return "Try logging in first you refreshed the page or you left the page idle for more than 10 minutes"

#route to show all the places from the db

@app.route("/showElecPlace", methods=["POST", "GET"])
@cross_origin()
def showElecPlace():
    try:
        username = request.json['username']
        persis_id = request.json['persis_id']
        print(db.session.find_one({'persis_id': persis_id}))
        if (db.session.find_one({'persis_id': persis_id})):
            if request.method == "POST":
                places = list(db.elecPlaces.find({}, {"_id" : 0}));
                #print(j[0]['placeName']) this is how to access the data
                trans = jsonify(places)
                return trans
        else:
            return "Try logging in first"
    except KeyError:
        db.session.delete_many({"username":username})
        return "Try logging in first you refreshed the page or you left the page idle for more than 10 minutes"

#to remove all the

@app.route("/clearPlace", methods=["POST", "GET"])
@cross_origin()
def clearPlace():
    try:
        username = request.json['username']
        persis_id = request.json['persis_id']
        if (db.session.find_one({'persis_id': persis_id})):
            if request.method == "POST":
                db.elecPlaces.remove()
                return "All places are removed successfully"
        else:
            return "Try logging in first"
    except KeyError:
        db.session.delete_many({"username":username})
        return "Try logging in first you refreshed the page or you left the page idle for more than 10 minutes"


#route for user login page rendering and processing

@app.route("/userLogin", methods=["GET", "POST"])
@cross_origin()
def userLogin():
    try:
        if request.method == "GET":
            return render_template("userLogin.html")
        if request.method == "POST":
            username = request.form["username"].strip()
            password = request.form["password"].strip()
            nameData = db.citizens.find_one({"email" : username})
            name = nameData["name"]
            if (db.session.find_one({'username' : username })):
                data = db.session.find_one({'username' : username })
                dbYear = data["dateLogin"][0]
                dbMonth = data["dateLogin"][1]
                dbDate = data["dateLogin"][2]
                dbHour = data["timeLogin"][0]
                dbMinute = data["timeLogin"][1]
                dbSecond = data["timeLogin"][2]
                print(dbYear, dbMonth, dbDate, dbHour, dbMinute, dbSecond)
                now = sessionTime()
                nowYear = now[0][0]
                nowMonth = now[0][1]
                nowDate = now[0][2]
                nowHour = now[1][0]
                nowMinute = now[1][1]
                nowSecond = now[1][2]
                a = dt.datetime(dbYear,dbMonth, dbDate, dbHour,dbMinute, dbSecond)
                b = dt.datetime(nowYear, nowMonth, nowDate, nowHour, nowMinute, nowSecond)
                duration = (b - a).total_seconds()
                print(duration)
                if ( duration > 180):
                    db.session.delete_many({"username": username})
                    if (db.onlineVotingCred.find_one({"username": username, "password": password, "vote" : 0})):
                        print("yahan pe")
                        dateTime = sessionTime()
                        dateNow = dateTime[0]
                        timeNow = dateTime[1]
                        resp = make_response(render_template('userSuccessLogin.html'))
                        cookie = token()
                        resp.set_cookie('persis_id', cookie, max_age=180)
                        resp.set_cookie("name", name.title(), max_age=60*60*24)
                        resp.set_cookie('username', username, max_age=10 * 365 * 24 * 60 * 60)
                        db.session.insert_one(
                            {"persis_id": cookie, "username": username, "dateLogin": dateNow, "timeLogin": timeNow})
                        return resp
                    elif (db.onlineVotingCred.find_one({"username": username, "password": password, "vote" : 1})):
                        error = "You already casted a vote"
                        return render_template("userLogin.html", error=error)
                    else:
                        error = "The login credentials entered by you are not valid"
                        return render_template("userLogin.html", error=error)
                else:
                    error = "If you didn't logged out properly wait for 3 minutes"
                    return render_template("userLogin.html", error=error)
            else:
                if (db.onlineVotingCred.find_one({"username": username, "password": password, "vote" : 0})):
                    dateTime = sessionTime()
                    dateNow = dateTime[0]
                    timeNow = dateTime[1]
                    resp = make_response(render_template('userSuccessLogin.html'))
                    cookie = token()
                    resp.set_cookie('persis_id', cookie, max_age=180)
                    resp.set_cookie("name", name.title(), max_age=60 * 60 * 24)
                    resp.set_cookie('username', username, max_age=10 * 365 * 24 * 60 * 60)
                    db.session.insert_one({"persis_id" : cookie, "username" : username, "dateLogin" : dateNow, "timeLogin" : timeNow})
                    return resp
                elif (db.onlineVotingCred.find_one({"username": username, "password": password, "vote": 1})):
                    error = "You already casted a vote"
                    return render_template("userLogin.html", error=error)
                else:
                    error = "The login credentials entered by you are not valid"
                    return render_template("userLogin.html", error=error)
    except NameError or ValueError or KeyError:
        db.session.delete_many({"username": username})
        resp = make_response(render_template("logout.html"))
        resp.set_cookie('persis_id', '', expires=0)
        return resp

#default route for vote now and password generation button

@app.route("/")
@cross_origin()
def main():
    return render_template("home.html")

#redirect route for userlogin directed from home button

@app.route("/homeLogin")
@cross_origin()
def login():
    return render_template("userLogin.html")


#redirect route for password generation directed from home button

@app.route("/homeGen")
@cross_origin()
def gen():
    return render_template("main.html")

#rendering of the main file when user leaves all the input feilds blank


@app.route("/blank")
@cross_origin()
def blank():
    error = "You cannot leave input fields empty"
    return render_template("main.html", error=error)


#login credentials page rendering and processing for ECI Admin

@app.route("/ECILogin" , methods=["POST", "GET"])
@cross_origin()
def ECILogin():
    try:
        if request.method == 'POST':
            username = (request.form["username"]).lower()
            if (db.session.find_one({'username' : username })):
                error = "One user is already logged in using your credentials"
                return render_template("ECILogin.html", error=error)
            else:
                username = (request.form["username"]).lower().strip()
                passwordInput = request.form["password"].strip()
                if ( username == cred.username and passwordInput == cred.password):
                    global otp
                    otp = password()
                    emailGen(cred.ECIEmail,otp)
                    resp = make_response(render_template('ECIOtp.html'))
                    resp.set_cookie('username' , username, max_age=10 * 365 * 24 * 60 * 60)
                    return resp
                else:
                    error = "Username and password provided by you is not correct"
                    return render_template("ECILogin.html", error=error)
        if request.method == "GET":
            return render_template("ECILogin.html")
    except KeyError or ValueError or NameError:
        error = "You cannot leave input field blank"
        return render_template("ECILogin.html", error=error)
    # except NameError:
        # error = "You pushed the back and you got log out, Try logging in again"
        # return render_template("ECILogin.html", error=error)



#otp verification route for ECI Admin login

@app.route("/otpVerify", methods=["POST", "GET"])
@cross_origin()
def otpVerify():
    # session.pop("user", None)
    try:
        if request.method == "POST":
            otpInput = request.form["otp"]
            if (type(otpInput) == None):
                return redirect(url_for("ECILogin"))
            if (otp == otpInput):
                username = request.cookies.get('username')
                resp = make_response(render_template('ECIHomePage.html'))
                cookie = token()
                resp.set_cookie('persis_id', cookie, max_age=600)
                if (db.session.find_one({"username" : username})):
                    data = db.session.find_one({"username" : username})
                    cookie = data["persis_id"]
                else:
                    db.session.insert_one({"persis_id": cookie, "username": username})
                return resp
            else:
                if len(otpInput) == 0:
                    error = "You cannot leave otp field blank, re-enter credentials to log in"
                    return render_template("ECIOtp.html", error=error)
                else:
                    error = "Enter correct OTP"
                    return render_template("ECIOtp.html", error=error)
        if (request.method == "GET"):
            return redirect(url_for("ECILogin"))
    except KeyError or ValueError or NameError:
        error = "Due to session time outage, you got logged out. Try logging in again"
        return render_template("ECILogin.html", error=error)

@app.route("/logout", methods=["GET", "POST"])
@cross_origin()
def logout():
    try:
        if request.method == "GET":
            return render_template("userLogin.html")
        if request.method == "POST":
            persis_id = request.cookies.get("persis_id")
            username = request.cookies.get("username")
            if(db.session.find_one({"persis_id": persis_id})):
                db.session.delete_many({"username" : username})
                resp = make_response(render_template("logout.html"))
                resp.set_cookie('persis_id', '', expires=0)
                return resp
            else:
                error = "You already got logged out"
                return render_template("logout.html", error = error)
    except KeyError or ValueError or NameError:
        error = "Due to session time outage, you got logged out. Try logging in again"
        return render_template("ECILogin.html", error=error)

#processing route for generating password for user

@app.route("/generate", methods=["GET", "POST"])
@cross_origin()
def generate():
    name = (request.form["name"]).lower()
    uid = request.form["uid"]
    dob = request.form["dob"]
    place = request.form["place"]
    error = "Thank you for using Online Voting, your login have been mailed to your registered email id!"
    success = "Thank you for using Online Voting, your login have been mailed to your registered email id!"
    if (len(name) == 0 or len(str(uid)) == 0 or len(dob) == 0 or len(place) == 0):
        error = "You cannot leave input fields blank"
        return redirect(url_for('blank'))
    else:
        name = (request.form["name"]).strip().lower()
        uid = int(request.form["uid"].strip())
        dob = request.form["dob"].strip()
        place = (request.form["place"]).strip()
        print(name, uid, dob, place)
        print(type(name), type(uid), type(dob), type(place))
        if( db.citizens.find_one({"name": name, "vid": uid, "dob" : dob, "pob" : place}) ):
            #accessing the particular persons data
            reqData = db.citizens.find_one({"name": name,"vid": uid, "dob" : dob, "pob" : place})
            # checking persons age
            dbDate = reqData["dob"]
            dbName = (reqData["name"]).title()
            dbEmail = reqData["email"]
            if (db.onlineVotingCred.find_one({"username" : dbEmail, "vote" : 1})):
                error = "You already voted. Thank you using Online Voting application "
                return render_template("main.html", error=error)
            ageNow = age(dbDate)
            if (ageNow >= 18 ):
                electPlace = reqData["pob"]
                if (db.elecPlaces.find_one({"placeName" : electPlace})):
                    #sending email procedure
                    to = reqData["email"]
                    print(to)
                    passwordGen = password()
                    emailGen(to, passwordGen, dbName)
                    return render_template("main.html", success=success)
                else:
                    error = "Elections are not happening at your place!"
                    print(error)
                    return render_template("main.html", error=error)
            else:
                error = "You are not eligible to vote, you should be atleast of 18 years in order to vote."
                print(error)
                return render_template("main.html", error=error)

        else:
            error = "The details given by you do not match our database"
            print(error)
            return render_template("main.html", error=error)
    # return render_template("success.html")

@app.errorhandler(404)
@cross_origin()
def pageNotFound(e):
    return render_template("error404.html"), 404

@app.errorhandler(500)
@cross_origin()
def internalServerError(e):
    return render_template("error500.html"), 500


@app.errorhandler(405)
@cross_origin()
def methodNotFound(e):
    return render_template("error405.html"), 405

app.run(debug=True)


