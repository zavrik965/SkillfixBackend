from flask import jsonify, request, abort, send_file, Response
from app.api import bp
from app.extensions import db
from app.models.user import User
from app.models.course import Course
from app.api.extensions import shifrator, renderMail, sendMail, create_payment, wait_payment, get_chunk
from config import Config
from threading import Thread
import os
import gc

@bp.route("/")
def index():
    return "API"

@bp.route("/auth", methods=["POST"])
def auth():
    data = request.json
    if not data or "login" not in data or "password" not in data:
        return jsonify({'is_auth': False}), 400
    #ans = database_request('SELECT id, confirmed, hashtoken FROM Users WHERE email="{}" and password="{}"'.format(data["login"], shifrator(data["password"])))
    user = User.query.filter(User.email == data.get("login")).filter(User.password == shifrator(data.get("password"))).all()
    
    if user:
        user = user[0]
        if user.confirmed:
            return jsonify({'is_auth': True, 'confirmed': True, 'token': user.hashtoken}), 200
        else:
            return jsonify({'is_auth': False, 'confirmed': False}), 401
    return jsonify({'is_auth': False, 'confirmed': False}), 401

@bp.route("/register", methods=["POST"])
def register():
    data = request.json
    if not data or "login" not in data or "password" not in data or "name" not in data:
        return jsonify({'is_register': False}), 400
    users = User.query.filter(User.email == data.get("login")).all()
    if users and users[0].confirmed == 1:
        return jsonify({'is_register': False}), 400
    elif users:
        user = users[0]
        user.password = shifrator(data.get("password"))
        user.name = data.get("name")
        message = renderMail("reg_email.html", page_address=Config.HOSTNAME + "/confirm?key=" + user.hashtoken)
        db.session.commit()
        sendMail(user.email, message, "Новая регистрация на Skillfix", Config.EMAIL, Config.EMAIL_PASSWORD)
        return jsonify({'is_register': True}), 200
    user = User(name=data.get("name"),
                payment_time="",
                email=data.get("login"),
                password=shifrator(data.get("password")),
                hashtoken=tokenizer(data.get("login")),
                confirmed=0,
                submited=0)
    message = renderMail("reg_email.html", page_address=Config.HOSTNAME + "/confirm?key=" + user.hashtoken)
    sendMail(user.email, message, "Новая регистрация на Skillfix", Config.EMAIL_PASSWORD, Config.EMAIL_PASSWORD)
    db.session.add(user)
    db.session.commit()
    return jsonify({'is_register': True}), 200

@bp.route("/forget_password", methods=["POST"])
def forget_password():
    data = request.json
    if not data or "login" not in data:
        return jsonify({'is_forgetted': False}), 400
    users = User.query.filter(User.email == data.get("login")).all()
    if users:
        user = users[0]
    else:
        return jsonify({'is_forgetted': False}), 404
    message = renderMail("forget_password_email.html", page_address=Config.HOSTNAME + "/repair_password?token=" + user.hashtoken)
    sendMail(user.email, message, "Восстановление пароля на Skillfix", Config.EMAIL, Config.EMAIL_PASSWORD)
    return jsonify({'is_forgetted': True}), 200

@bp.route("/repair_password", methods=["POST"])
def repair_password():
    data = request.json
    if not data or "token" not in data or "password" not in data:
        return jsonify({'is_repaired': False}), 400
    users = User.query.filter(User.hashtoken == data.get("token")).all()
    if users:
        user = users[0]
        user.password = shifrator(data.get("password"))
        db.session.commit()
        return jsonify({"is_repaired": True}), 200
    return jsonify({"is_repaired": False}), 401

@bp.route("/confirm", methods=["POST"])
def confirm():
    data = request.json
    if not data or "token" not in data:
        return jsonify({"is_confirmed": False}), 400
    users = User.query.filter(User.hashtoken == data.get("token")).all()
    if users:
        user = users[0]
        user.confirmed = 1
        db.session.commit()
        return jsonify({"is_confirmed": True}), 200
    return jsonify({"is_confirmed": False}), 401

@bp.route("/get_courses", methods=["GET"])
def get_courses():
    raw_courses = Course.query.all()
    courses = []
    for course in raw_courses:
        data = {"id": course.id,
                "name": course.name,
                "previewphoto": Config.DOMEN + "/" + course.previewphoto,
                "category": course.category}
        courses.append(data)
    return jsonify(courses), 200

@bp.route("/get_course/<id>", methods=["GET"])
def get_course(id):
    raw_course = Course.query.filter(Course.id == id).one()
    lessons = json.loads(raw_course.lessons)
    list_lessons = [{"id": 0, "num": f"Превью", "title": "Превью", "url": raw_course.previewvideo}]
    for i in range(len(lessons)):
        list_lessons.append({"id": i + 1, "num": f"Урок {i + 1}:", "title": list(lessons.keys())[i], "url": Config.DOMEN + "/" + list(lessons.values())[i]})
    course = {"id": raw_course.id,
              "name": raw_course.name,
              "author": raw_course.author,
              "authorinfo": raw_course.authorinfo,
              "expertphoto": Config.DOMEN + "/" + raw_course.expertphoto,
              "previewphoto": Config.DOMEN + "/" + raw_course.previewphoto,
              "previewvideo": Config.DOMEN + "/" + raw_course.previewvideo,
              "lessons": list_lessons,
              "category": raw_course.category,
              "description": raw_course.description,
              "duration": raw_course.duration}
    return jsonify(course), 200

@bp.route("/set_submited", methods=["POST"])
def set_submited():
    data = request.json
    if not data or "login" not in data:
        return jsonify({'is_submited': False}), 400
    users = User.query.filter(User.email == data.get("login")).all()
    if users:
        confirmation_url, payment_id = create_payment()
        Thread(target=wait_payment, args=(payment_id, users[0])).start()
        return jsonify({"is_created_payment": True, "confirmation_url": confirmation_url}), 200
    return jsonify({"is_submited": False}), 401

@bp.route("/get_submited", methods=["POST"])
def get_submited():
    data = request.json
    if not data or "login" not in data:
        return jsonify({'is_submited': False}), 400
    users = User.query.filter(User.email == data.get("login")).all()
    if users:
        user = users[0]
        if not user.submited:
            return jsonify({"is_submited": False}), 403
        return jsonify({"is_submited": True}), 200
    return jsonify({"is_submited": False}), 401

@bp.route("/add_submit", methods=["POST"])
def add_submite():
    data = request.json
    if not data or "login" not in data or "course" not in data or "name" not in data:
        return jsonify({'is_submited': False}), 400
    while os.path.exists("lock_submite"):
        pass
    open("lock_submite", "w")
    prev = open("users_submits.txt").read()
    with open("users_submits.txt", "w") as f:
        f.write(prev + f"{data.get('name')} [{data.get('login')}]: {data.get('course')}\n")
    os.remove("lock_submite")
    return jsonify({"is_submited": True}), 

@bp.route('/pic/<filename>')
def get_pic(filename):
    if not os.path.isfile("app/api/pic/" + filename):
        abort(404)
    return send_file("api/pic/" + filename, as_attachment=True)

@bp.after_request
def after_request(response):
    response.headers.add('Accept-Ranges', 'bytes')
    return response

@bp.route('/video/<filename>')
def get_file(filename):
    range_header = request.headers.get('Range', None)
    byte1, byte2 = 0, None
    if range_header:
        match = re.search(r'(\d+)-(\d*)', range_header)
        groups = match.groups()

        if groups[0]:
            byte1 = int(groups[0])
        if groups[1]:
            byte2 = int(groups[1])
    
    chunk, start, length, file_size = get_chunk(filename, byte1, byte2)
    resp = Response(chunk, 206, mimetype='video/mp4',
                      content_type='video/mp4', direct_passthrough=True)
    del chunk
    gc.collect()
    resp.headers.add('Content-Range', 'bytes {0}-{1}/{2}'.format(start, start + length - 1, file_size))
    return resp