import os
from flask import Flask, render_template, url_for, redirect, request, send_file, session, make_response
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from datetime import datetime
from flask_wtf import FlaskForm 
from wtforms import StringField, PasswordField, BooleanField, TextAreaField, SubmitField, RadioField, DateField, SelectField, IntegerField
from wtforms.validators import InputRequired, Email, Length, EqualTo, ValidationError
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_mail import Mail, Message
from io import BytesIO
from werkzeug.security import generate_password_hash, check_password_hash
# from sqlalchemy import text
import pdfkit

app = Flask(__name__)

BASEDIR=os.path.abspath(os.path.dirname(__file__))
app.config['SECRET_KEY']='thisisasecret'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS']=False
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///'+ os.path.join(BASEDIR,'SARdbase.sqlite')
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
app.config.update(
    DEBUG=True,
    #EMAIL SETTINGS
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT=465,
    MAIL_USE_SSL=True,
    MAIL_USERNAME = 'projectSARmail@gmail.com',
    MAIL_PASSWORD = '#####'
    )

mail = Mail(app)
bootstrap = Bootstrap(app)
db=SQLAlchemy(app)
admin = Admin(app, name='SAR', template_mode='bootstrap3')
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'logintype'


class UserType(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(15), unique=True)
    email = db.Column(db.String(50), unique=True)
    password = db.Column(db.String(80))
    usertype = db.Column(db.String(15))

class Class_(db.Model):
        __tablename__ = 'class_'
        id = db.Column(db.Integer,primary_key=True)
        name =db.Column(db.String(200))
        subjects = db.relationship('Subject', backref='class_', lazy=True)
        students = db.relationship('Student', backref='class_', lazy=True)

        def __repr__(self) :
                return self.name


class Subject(db.Model):
        id = db.Column(db.Integer,primary_key=True)
        name =db.Column(db.String(200))
        class_id = db.Column(db.Integer, db.ForeignKey('class_.id'), nullable=False)
        teacher_id = db.Column(db.Integer, db.ForeignKey('teacher.id'), nullable=False)
        lectures = db.relationship('Lecture', backref='subject', lazy=True)
        attendance = db.relationship('Attendance', backref='subject', lazy='dynamic', uselist=True)

        def __repr__(self) :
                return self.name + ' - ' +self.class_.name


class Teacher(db.Model):
        id = db.Column(db.Integer,primary_key=True)
        name =db.Column(db.String(200))
        email =db.Column(db.String(200))
        password = db.Column(db.String(200))
        subjects = db.relationship('Subject', backref='teacher', lazy=True)
        lectures = db.relationship('Lecture', backref='teacher', lazy=True)

        def __repr__(self) :
                return self.name


class Student(db.Model) :
        id = db.Column(db.Integer, primary_key=True)
        name =db.Column(db.String(200))
        email =db.Column(db.String(200))
        password = db.Column(db.String(200))
        class_id = db.Column(db.Integer, db.ForeignKey('class_.id'), nullable=False)
        attendance = db.relationship('Attendance', backref='student', lazy='dynamic', uselist=True)

        def __repr__(self) :
                return self.name


class Attendance(db.Model) :
        id = db.Column(db.Integer, primary_key=True)
        status = db.Column(db.Boolean)
        lecture_id = db.Column(db.Integer, db.ForeignKey('lecture.id'), nullable=False)
        student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
        subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)

        def __repr__(self) :
                return str(self.lecture) + ' ' + str(self.status)


class Lecture(db.Model) :
        id = db.Column(db.Integer, primary_key=True)
        start_time = db.Column (db.DateTime())
        stop_time = db.Column(db.DateTime())
        subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)
        teacher_id = db.Column(db.Integer, db.ForeignKey('teacher.id'), nullable=False)
        attendance = db.relationship('Attendance', backref='lecture', lazy='dynamic', uselist=True)

        def __repr__(self) :
                return self.subject.name + ' - ' + self.teacher.name + ' -' + self.start_time.strftime('%b %d,%I:%M %p')+' - '+self.stop_time.strftime('%b %d,%I:%M %p')

class UploadFile(db.Model):
    id= db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(300))
    data = db.Column(db.LargeBinary)

class TimeTable(db.Model):
    id= db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(300))
    data = db.Column(db.LargeBinary)

class Syllabus(db.Model):
    id= db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(300))
    data = db.Column(db.LargeBinary)    

class Notice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(50))
    subtitle = db.Column(db.String(50))
    name = db.Column(db.String(20))
    date_posted = db.Column(db.DateTime)
    content = db.Column(db.Text)    

class Schedule(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(200))
    complete = db.Column(db.Boolean)

    def __repr__(self) :
                return self.id


class UserForm(FlaskForm):
    username = StringField('Username', validators=[InputRequired(), Length(min=4, max=15)])
    email = StringField('Email', validators=[InputRequired(), Email(message='Invalid email'), Length(max=50)])
    password = PasswordField('Password', validators=[InputRequired(), Length(min=8, max=80)])
    usertype = SelectField('UserType', choices=[('admin', 'admin'), ('teacher', 'teacher')], validators=[InputRequired(), Length(min=4, max=15)])

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[InputRequired(), Length(min=4, max=15)])
    password = PasswordField('Password', validators=[InputRequired(), Length(min=8, max=80)])
    remember = BooleanField('Remember me')

class CheckAttendanceForm(FlaskForm):
    student = SelectField('Student')
    submit_btn = SubmitField('Submit')

class ClassForm(FlaskForm) :
    class_ = SelectField('Class')
    submit_btn = SubmitField('Select Class')

class LectureForm(FlaskForm) :
    start_time = StringField('Start Time')
    subject = SelectField('Subject')
    teacher = SelectField('Teacher')
    stop_time = StringField('End Time')
    submit_btn = SubmitField('Submit')

class BlacklistForm(FlaskForm):
    class_ = SelectField('Class')
    percentage=IntegerField('Percetage', validators=[InputRequired()])

class TeacherForm(FlaskForm):
    name = StringField('name', validators=[InputRequired(), Length(min=4, max=15)])
    email = StringField('email', validators=[InputRequired(), Email(message='Invalid email'), Length(max=50)])

class FeedbackForm(FlaskForm):
    yourname = StringField('Your Name', validators=[InputRequired(), Length(min=4, max=100)])
    feedback = TextAreaField('Feedback', validators=[InputRequired(), Length(min=8, max=100)])    

class ContactUsForm(FlaskForm):
    yourname = StringField('Your Name', validators=[InputRequired(), Length(min=4, max=100)])
    feedback = TextAreaField('Message', validators=[InputRequired(), Length(min=8, max=80)])    

# @app.route('/sql')
# def sql():
#     sql = ("SELECT id FROM student WHERE name='student1'").fetchall()
#     result = db.engine.execute(sql)
#     for fetch in result:
#       fetched= fetch[0]
#     #print result
#     #str_result= str(result)
#     return render_template("sql.html", result=result)

@app.route('/')
def homepage():
	return render_template("homepage.html")

@app.route('/adduser', methods=['GET', 'POST'])
@login_required
def adduser():
    form = UserForm()

    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data, method='sha256')
        new_user = UserType(username=form.username.data, email=form.email.data, password=hashed_password, usertype=form.usertype.data)
        db.session.add(new_user)
        db.session.commit()
        if form.usertype.data == 'admin':
            return '<h1>New Admin has been created!</h1></br><a href=''/adminui''>Click here to go back to main page</a>'
        else:
            return redirect(url_for('addteacher')) 
        #return '<h1>New user has been created!</h1>'
        #return '<h1>' + form.username.data + ' ' + form.email.data + ' ' + form.password.data + '</h1>'

    return render_template('adduser.html', form=form)

@login_manager.user_loader
def load_user(user_id):
    return UserType.query.get(int(user_id))   

@app.route('/logintype', methods=['GET', 'POST'])
def logintype():
    form = LoginForm()

    if form.validate_on_submit():
        user = UserType.query.filter_by(username=form.username.data).first()
        if user:
            if check_password_hash(user.password, form.password.data):
                login_user(user, remember=form.remember.data)
                if user.usertype == 'admin':
                   return redirect(url_for('adminui'))
                else:
                   return redirect(url_for('teacherui'))      

        return '<h1>Invalid username or password</h1>'
        #return '<h1>' + form.username.data + ' ' + form.password.data + '</h1>'
        
    return render_template('loginform.html', form=form)


@app.route('/adminui')
@login_required
def adminui():
    return render_template('adminui.html', name=current_user.username)    


@app.route('/addteacher', methods=['GET', 'POST'])
@login_required
def addteacher():
    form = TeacherForm()

    if form.validate_on_submit():
      new_teacher = Teacher(name=form.name.data, email=form.email.data)
      db.session.add(new_teacher)
      db.session.commit()
      return '<h1>New teacher has been created!</h1></br><a href=''/adminui''>Click here to go back to main page</a>'
    return render_template('addteacher.html', form=form)      

@app.route('/teacherui')
@login_required
def teacherui():
    return render_template('teacherui.html', name=current_user.username)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('homepage'))        

@app.route('/select-class/', methods=['GET', 'POST'])
@login_required
def select_class() :
        form = ClassForm()
        classes = Class_.query.all()
        form.class_.choices = [(str(c.id), c.name) for c in classes]

        if form.validate_on_submit() :
                c = form.class_.data
                print(c)
                session['class_id'] = c
                return redirect(url_for('take_attendance'))

        return render_template('selectClass.html', form=form)


@app.route('/take-attendance/', methods=['GET', 'POST'])
@login_required
def take_attendance():
        form = LectureForm()
        c = Class_.query.get(session['class_id'])
        form.subject.choices = [(str(s.id), s.name) for s in c.subjects]
        teachers = Teacher.query.all()
        form.teacher.choices = [(str(t.id), t.name) for t in teachers]

        if form.validate_on_submit() :
                print('validated')
                sub_id = form.subject.data
                teach_id = form.teacher.data

                start_time_str = form.start_time.data
                stop_time_str = form.stop_time.data

                subject = Subject.query.get(sub_id)
                teacher = Teacher.query.get(teach_id)
                
                hour, minute = int(start_time_str[0:2]), int(start_time_str[3:])
                start_time = datetime.now().replace(hour=hour, minute=minute, second=0)
                hour, minute = int(stop_time_str[0:2]), int(stop_time_str[3:])
                stop_time = datetime.now().replace(hour=hour, minute=minute, second=0)
                lecture = Lecture(start_time=start_time, stop_time=stop_time, subject=subject, teacher=teacher)
                db.session.add(lecture)
                db.session.commit()
                return redirect(url_for('student_list', id=lecture.id))

        return render_template("takeAttendance.html", form=form)


@app.route('/take-lecture/<int:id>/', methods=['GET', 'POST'])
@login_required
def student_list(id) :
        lecture = Lecture.query.get(id)
        subject = lecture.subject
        students = lecture.subject.class_.students
        if request.method == 'POST' :
                print(request.form)
                formvals = request.form.to_dict()
                for student_id, val in formvals.items() :
                        status = 1 if val == 'on' else 0
                        print(student_id, val, status)
                        student = Student.query.get(student_id)
                        a = Attendance(lecture=lecture, student=student,status=status, subject=subject)
                        print(a)
                        db.session.add(a)

                db.session.commit()
                return render_template('attendancerecorded.html')
        return render_template('takeLecture.html', students=students)


@app.route('/checkAttendance/',methods=['GET','POST'])
def checkAtten():
        form = ClassForm()

        classes = Class_.query.all()
        form.class_.choices = [(str(c.id), c.name) for c in classes]

        if form.validate_on_submit() :
                c = form.class_.data
                print(c)
                session['class_id_att'] = c
                return redirect(url_for('get_attendance'))

        return render_template('selectClass.html', form=form)


@app.route('/get_attendance/',methods=['GET','POST'])
def get_attendance():
    c= session['class_id_att']
    cl=Class_.query.get(c)
    students= cl.students
   # print(students)
    return render_template('get_attendance.html',students=students)

@app.route('/showAttendance/<int:id>/')
def showAtten(id):
        stud = Student.query.get_or_404(id)
        class_ = stud.class_
        att_list = []

        for sub in class_.subjects :
                print(sub)
                present = stud.attendance.filter_by(subject=sub, status=1).count()
                print(present)
                total = stud.attendance.filter_by(subject=sub).count()
                print(total)
                if present!=0:
                  percent = (100.0 * present)/total
                  if percent <= 75:
                    trclass='table-danger'
                  else:
                    trclass='table-success'  
                else:
                  percent=0
                  trclass='table-danger'
                att_list.append([sub.name, present, total, percent, trclass])
        for a in att_list :
            print(a)

        return render_template("showAtten.html", att_list = att_list, stud=stud)

@app.route('/createblacklist', methods=['GET', 'POST'])
@login_required
def createblacklist():
    form=BlacklistForm()
    classes = Class_.query.all()
    form.class_.choices = [(str(c.id), c.name) for c in classes]
    print('before')
    if form.validate_on_submit():
        print('validated')
        c = form.class_.data
        per=form.percentage.data
        session['per'] = per
        session['class_id'] = c
        return redirect(url_for('blacklist'))
    return render_template('createblacklist.html', form=form)   

@app.route('/blacklist', methods=['GET', 'POST'])
@login_required
def blacklist():
    per= session['per']
    c= session['class_id']
    cl=Class_.query.get(c)
    students= cl.students
    b_stud_list = []
    for stud in students:
        for sub in cl.subjects:
            present = stud.attendance.filter_by(subject=sub, status=1).count()
            total = stud.attendance.filter_by(subject=sub).count()
            if present!=0:
              percent = (100.0 * present)/total
              if percent <= per:
                b_stud=stud
                b_sub=sub
                b_stud_list.append([b_sub.name, b_stud.name, percent])
            else:
              percent=0 
              b_stud=stud
              b_sub=sub
              b_stud_list.append([b_sub.name, b_stud.name, percent])
    for a in b_stud_list :
            print(a)  
    # config = pdfkit.configuration(wkhtmltopdf="C:\\Program Files\\wkhtmltopdf\\bin\\wkhtmltopdf.exe")
    # rendered = render_template("blacklist.html", stud_list = stud_list, cl=cl)
    # pdf= pdfkit.from_string(rendered, False, configuration=config)
    # response= make_response(pdf)
    # response.headers['Content-Type'] = 'application/pdf'
    # response.headers['Content-Disposition']= 'inline; filename=blacklist.pdf'
    # return response 
    session['b_stud_list']=b_stud_list                   
    return render_template("blacklist.html", b_stud_list = b_stud_list, cl=cl)

@app.route('/downloadblacklist', methods=['GET', 'POST'])
@login_required
def downloadblacklist():
    b_stud_list= session['b_stud_list']
    c= session['class_id']
    cl=Class_.query.get(c)
    config = pdfkit.configuration(wkhtmltopdf="wkhtmltopdf.exe")
    rendered = render_template("blacklists.html", b_stud_list = b_stud_list, cl=cl)
    pdf= pdfkit.from_string(rendered, False, configuration=config)
    response= make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition']= 'attachment; filename=blacklist.pdf'
    return response

@app.route('/createreport', methods=['GET', 'POST'])
@login_required
def createreport():
    form=ClassForm()
    classes = Class_.query.all()
    form.class_.choices = [(str(c.id), c.name) for c in classes]
    #print('before')
    if form.validate_on_submit():
        #print('validated')
        c = form.class_.data
        session['class_id'] = c
        return redirect(url_for('report'))
    return render_template('createreport.html', form=form) 

@app.route('/report')
@login_required
def report():
    c= session['class_id']
    cl=Class_.query.get(c)
    students= cl.students
    less_25=0
    less_50=0
    less_75=0
    hundred=0
    stud_list = []
    for stud in students:        
            present = stud.attendance.filter_by( status=1).count()
            total = stud.attendance.count()
            if present!=0:
              percent = (100.0 * present)/total
              # if percent <= per:
              b_stud=stud
              if percent <= 75:
                trclass='table-danger'
              else:
                trclass='success'  
              stud_list.append([ b_stud.name, present, total, percent, trclass])
            else:
              percent=0 
              b_stud=stud
              trclass='table-danger'
              stud_list.append([b_stud.name, present, total, percent, trclass])
            if percent <= 25:
              less_25+=1 
            if percent <= 50:
              less_50+=1
            if percent <= 75:
              less_75+=1
            if percent ==100:
              hundred+=1      
    for a in stud_list :
            print(a)  
    session['less_25']=less_25
    session['less_50']=less_50
    session['less_75']=less_75
    session['hundred']=hundred
    session['stud_list']=stud_list
    # config = pdfkit.configuration(wkhtmltopdf="C:\\Program Files\\wkhtmltopdf\\bin\\wkhtmltopdf.exe")
    # rendered = render_template('report.html', stud_list = stud_list, cl=cl, less_25=less_25, less_75=less_75, less_50=less_50, hundred=hundred)
    # pdf= pdfkit.from_string(rendered, False, configuration=config)
    # response= make_response(pdf)
    # response.headers['Content-Type'] = 'application/pdf'
    # response.headers['Content-Disposition']= 'attachment; filename=report.pdf'
    return render_template('report.html', stud_list = stud_list, cl=cl, less_25=less_25, less_75=less_75, less_50=less_50, hundred=hundred)

@app.route('/downloadreport', methods=['GET', 'POST'])
@login_required
def downloadreport():
    stud_list= session['stud_list']
    c= session['class_id']
    less_25= session['less_25']
    less_50= session['less_50']
    less_75= session['less_75']
    hundred= session['hundred']
    cl=Class_.query.get(c)
    config = pdfkit.configuration(wkhtmltopdf="C:\\Program Files\\wkhtmltopdf\\bin\\wkhtmltopdf.exe")
    rendered = render_template('reports.html', stud_list = stud_list, cl=cl, less_25=less_25, less_75=less_75, less_50=less_50, hundred=hundred)
    pdf= pdfkit.from_string(rendered, False, configuration=config)
    response= make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition']= 'attachment; filename=report.pdf'
    return response

@app.route('/uploadfile', methods=['GET', 'POST'])
@login_required
def uploadfile():
    if request.method =='POST':
        file = request.files['inputFile']

        newFile = UploadFile(name=file.filename, data=file.read())
        db.session.add(newFile)
        db.session.commit()
        return 'Saved ' + file.filename + ' to the database!'
    return render_template('uploadfiles.html')

@app.route('/downloadfiles')
def downloadfiles() :
    files = UploadFile.query.all()
    return render_template('downloadfiles.html', files=files)

@app.route('/downloadfile/<int:post_id>')
def downloadfile(post_id):
    file_data = UploadFile.query.filter_by(id=post_id).first()
    return send_file(BytesIO(file_data.data), attachment_filename=file_data.name ,as_attachment=True) 

@app.route('/uploadsyllabus', methods=['GET', 'POST'])
@login_required
def uploadsyllabus():
    if request.method =='POST':
        file = request.files['inputFile']

        newFile = Syllabus(name=file.filename, data=file.read())
        db.session.add(newFile)
        db.session.commit()
        return 'Saved ' + file.filename + ' to the database!'
    return render_template('uploadsyllabus.html')

@app.route('/downloadsyllabus/')
def downloadsyllabus() :
    syllabuss = Syllabus.query.all()

    return render_template('downloadsyllabus.html', syllabuss=syllabuss)

@app.route('/syllabus/<int:post_id>')
def syllabus(post_id):
    file_data = Syllabus.query.filter_by(id=post_id).first()
    return send_file(BytesIO(file_data.data), attachment_filename=file_data.name ,as_attachment=True)   


@app.route('/uploadtt', methods=['GET', 'POST'])
@login_required
def uploadtt():
    if request.method =='POST':
        file = request.files['inputFile']

        newFile = TimeTable(name=file.filename, data=file.read())
        db.session.add(newFile)
        db.session.commit()
        return 'Saved ' + file.filename + ' to the database!'
    return render_template('uploadtt.html')

@app.route('/downloadtt/')
def downloadtt() :
    timetables = TimeTable.query.all()

    return render_template('downloadtt.html', timetables=timetables)

@app.route('/timetable/<int:post_id>')
def timetable(post_id):
    file_data = TimeTable.query.filter_by(id=post_id).first()
    return send_file(BytesIO(file_data.data), attachment_filename=file_data.name,as_attachment=True)   

    @app.route('/checknotice')
    def checknotice():
        posts = Notice.query.order_by(Notice.date_posted.desc()).all()
      
        return render_template('checknotice.html', posts=posts)

@app.route('/postnotice/<int:post_id>')
def postnotice(post_id):
    post = Notice.query.filter_by(id=post_id).one()

    return render_template('postnotice.html', post=post)

@app.route('/addnotice')
@login_required
def addnoticee():
    return render_template('addnotice.html')

@app.route('/addpost', methods=['POST'])
@login_required
def addpost():
    title = request.form['title']
    subtitle = request.form['subtitle']
    name= request.form['name']
    content = request.form['content']

    post = Notice(title=title, subtitle=subtitle, name=name, content=content, date_posted=datetime.now())

    db.session.add(post)
    db.session.commit()

    return render_template('success.html')

@app.route('/schedule')
@login_required
def index():
    incomplete = Schedule.query.filter_by(complete=False).all()
    complete = Schedule.query.filter_by(complete=True).all()

    return render_template('index.html', incomplete=incomplete, complete=complete)

@app.route('/add', methods=['POST'])
def add():
    work = Schedule(text=request.form['todotask'], complete=False)
    db.session.add(work)
    db.session.commit()

    return redirect(url_for('index'))

@app.route('/complete/<id>')
def complete(id):

    work = Schedule.query.filter_by(id=int(id)).first()
    work.complete = True
    db.session.commit()
    
    return redirect(url_for('index'))

@app.route('/incomplete/<id>')
def incomplete(id):

    work = Schedule.query.filter_by(id=int(id)).first()
    work.incomplete= True
    db.session.commit()


    return redirect(url_for('index'))

def test_foo(self):
        pass

@app.route('/feedback', methods=['GET', 'POST'])
def feedback():
    form = FeedbackForm(request.form)
 
    if form.validate_on_submit():
       msg = Message(form.yourname.data,
        sender="projectSARmail@gmail.com",
        recipients=['rhutujashevde@gmail.com'])
       msg.body = 'By '+form.yourname.data+',\n'+form.feedback.data           
       mail.send(msg)
       return render_template('mailsent.html')
    return render_template('feedback.html', form=form)
    
@app.route('/contactus', methods=['GET', 'POST'])
def contactus():
    form = ContactUsForm(request.form)
 
    if form.validate_on_submit():
       msg = Message(form.yourname.data,
        sender="projectSARmail@gmail.com",
        recipients=['greataakarshan@gmail.com'])
       msg.body = 'By '+form.yourname.data+',\n'+form.feedback.data           
       mail.send(msg)
       return render_template('mailsent.html')
    return render_template('contactus.html', form=form)       

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/aboutSAR')
def aboutSAR():
    return render_template('aboutSAR.html')    

db.create_all()


admin.add_view(ModelView(Teacher, db.session))
admin.add_view(ModelView(Student, db.session))
admin.add_view(ModelView(Class_, db.session))
admin.add_view(ModelView(Subject, db.session))
admin.add_view(ModelView(Attendance, db.session))
admin.add_view(ModelView(Lecture, db.session))


if __name__ == '__main__':
	app.jinja_env.auto_reload = True
	app.run(port=8000,debug=True)
