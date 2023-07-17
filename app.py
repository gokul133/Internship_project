import sqlite3
import os, json
from flask import Flask, render_template, request, flash, redirect, url_for, jsonify
from flask_login import logout_user, login_required, LoginManager, UserMixin, login_user, current_user
from werkzeug.utils import secure_filename
from io import BytesIO


app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

login_manager = LoginManager(app)
login_manager.login_view = 'login'


class User(UserMixin):
    def __init__(self, id):
        self.id = id


@login_manager.user_loader
def load_user(user_id):
    return User(user_id)


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        connection = sqlite3.connect("instance/data.db")
        cursor = connection.cursor()
        name = request.form['name']
        password = request.form['password']
        role = request.form['role']
        if role == 'student':
            query = "SELECT username, password FROM username WHERE username=? and password=?"
            cursor.execute(query, (name, password))
            results = cursor.fetchall()
            if len(results) == 0:
                flash("Please try again!!!", "error")
                return redirect(url_for('login'))
            user = User(name)
            login_user(user)
            return redirect(url_for('student_profile'))

        elif role == 'teacher':
            query = "SELECT username, password FROM adminuser WHERE username=? and password=?"
            cursor.execute(query, (name, password))
            results = cursor.fetchall()
            if len(results) == 0:
                flash("Please try again!!!", "error")
                return redirect(url_for('login'))
            user = User(name)
            login_user(user)
            return redirect(url_for('teacher'))
    return render_template('login.html')


@app.route('/student')
@login_required
def student():
    return render_template('student.html')


@app.route('/teacher')
@login_required
def teacher():
    return render_template('teacher.html')


@app.route('/create_quiz', methods=['GET', 'POST'])
@login_required
def create_quiz():
    if request.method == 'POST':
        connection = sqlite3.connect("instance/data.db")
        cursor = connection.cursor()

        exam_code = request.form['examCode']
        num_questions = int(request.form['numQuestions'])

        for i in range(1, num_questions + 1):
            question = request.form['question' + str(i)]
            choices = []
            for j in range(1, 5):
                choices.append(request.form['choice' + str(j)])

            correct_answer = request.form['correctAnswer']

            # Store the quiz information in the database
            query = "INSERT INTO quiz (exam_code, question, choice1, choice2, choice3, choice4, crct_choice) " \
                    "VALUES (?, ?, ?, ?, ?, ?, ?)"
            cursor.execute(query, (exam_code, question, choices[0], choices[1], choices[2], choices[3], correct_answer))
            connection.commit()

        flash("Quiz created successfully!", "success")
        return redirect(url_for('teacher'))

    return render_template('create_quiz.html')



@app.route('/create_exam', methods=['GET', 'POST'])
@login_required
def create_exam():
    if request.method == 'POST':
        connection = sqlite3.connect("instance/data.db")
        cursor = connection.cursor()

        exam_code = request.form['examCode']
        num_questions = request.form['numQuestions']

        # Validate the numQuestions input
        if not num_questions.isdigit():
            flash("Please enter a valid number for the number of questions.", "error")
            return redirect(url_for('teacher'))

        num_questions = int(num_questions)

        for i in range(1, num_questions + 1):
            question = request.form['question' + str(i)]

            # Store the quiz information in the database
            query = "INSERT INTO exam (exam_code, question) " \
                    "VALUES (?, ?)"
            cursor.execute(query, (exam_code, question))
            connection.commit()

        flash("Exam created successfully!", "success")
        return redirect(url_for('teacher'))

    return render_template('create_exam.html')



@app.route('/student_profile')
@login_required
def student_profile():
    # Retrieve student profile details from the database
    connection = sqlite3.connect("instance/data.db")
    cursor = connection.cursor()
    query = "SELECT username, dept, mail, mobile_no, D_O_B FROM username WHERE username = ?"
    cursor.execute(query, (current_user.id,))
    result = cursor.fetchone()

    if result:
        username, dept, mail, mobile_no, DOB = result
        return render_template('student_profile.html', username=username, dept=dept, mail=mail, mobile_no=mobile_no, DOB=DOB)
    else:
        flash("Student profile not found.", "error")
        return redirect(url_for('login'))


@app.route('/check_exam_code')
@login_required
def check_exam_code():
    exam_code = request.args.get('examCode')

    connection = sqlite3.connect("instance/data.db")
    cursor = connection.cursor()

    # Check if the exam code already exists
    query = "SELECT * FROM quiz WHERE exam_code = ?"
    cursor.execute(query, (exam_code,))
    result = cursor.fetchone()

    if result:
        exists = True
    else:
        exists = False

    response = {"exists": exists}
    return jsonify(response)


@app.route('/check_exam_code1')
@login_required
def check_exam_code1():
    exam_code = request.args.get('examCode')

    connection = sqlite3.connect("instance/data.db")
    cursor = connection.cursor()

    # Check if the exam code already exists
    query = "SELECT * FROM exam WHERE exam_code = ?"
    cursor.execute(query, (exam_code,))
    result = cursor.fetchone()

    if result:
        exists = True
    else:
        exists = False

    response = {"exists": exists}
    return jsonify(response)


@app.route('/retrieve_questions')
@login_required
def retrieve_questions():
    exam_code = request.args.get('examCode')

    connection = sqlite3.connect("instance/data.db")
    cursor = connection.cursor()

    # Check if the user has already taken the quiz
    username = current_user.id
    query = "SELECT * FROM marks WHERE username = ? AND exam_code = ?"
    cursor.execute(query, (username, exam_code))
    result = cursor.fetchone()

    if result:
        # flash("You've already attended the quiz.", "info")
        response = {"questions": None}  # Set questions to None
        return jsonify(response)

    # Retrieve questions for the given exam code
    query = "SELECT question, choice1, choice2, choice3, choice4, crct_choice FROM quiz WHERE exam_code = ?"
    cursor.execute(query, (exam_code,))
    results = cursor.fetchall()

    if not results:
        # flash("No questions found for the entered exam code.", "error")
        response = {"questions": None}  # Set questions to None
        return jsonify(response)

    questions = []
    for row in results:
        question = {
            "question": row[0],
            "options": [row[1], row[2], row[3], row[4]],
            "correct_answer": row[5]  # Add correct answer to the question details
        }
        questions.append(question)

    response = {"questions": questions}
    return jsonify(response)


@app.route('/retrieve_questions1')
@login_required
def retrieve_questions1():
    exam_code = request.args.get('examCode')

    connection = sqlite3.connect("instance/data.db")
    cursor = connection.cursor()

    # Check if the user has already taken the quiz
    username = current_user.id
    query = "SELECT * FROM exam_submission WHERE username = ? AND exam_code = ?"
    cursor.execute(query, (username, exam_code))
    result = cursor.fetchone()

    if result:
        flash("You've already attended the quiz.", "info")
        response = {"questions": None}  # Set questions to None
        return jsonify(response)

    # Retrieve questions for the given exam code
    query = "SELECT question FROM exam WHERE exam_code = ?"
    cursor.execute(query, (exam_code,))
    results = cursor.fetchall()

    if not results:
        flash("No questions found for the entered exam code.", "error")
        response = {"questions": None}  # Set questions to None
        return jsonify(response)

    questions = []
    for row in results:
        question = {
            "question": row[0],
        }
        questions.append(question)

    response = {"questions": questions}
    return jsonify(response)


@app.route('/submit_quiz', methods=['POST'])
@login_required
def submit_quiz():
    data = request.get_json()
    answers = data.get('answers', {})  # Dictionary to store the user's selected answers for each question
    exam_code = data.get('examCode')

    # Retrieve the correct answers for the submitted exam code
    connection = sqlite3.connect("instance/data.db")
    cursor = connection.cursor()
    query = "SELECT crct_choice FROM quiz WHERE exam_code = ?"
    cursor.execute(query, (exam_code,))
    correct_answers = [row[0] for row in cursor.fetchall()]

    # Calculate the marks
    total_marks = 0
    for question_number, correct_answer in enumerate(correct_answers, 1):
        user_answer = answers.get('answer' + str(question_number))
        if user_answer == correct_answer:
            total_marks += 1

    # Store the marks in the database
    username = current_user.id
    query = "INSERT INTO marks (username, exam_code, marks) VALUES (?, ?, ?)"
    cursor.execute(query, (username, exam_code, total_marks))
    connection.commit()

    flash(f"You scored {total_marks} marks!", "success")
    return jsonify({"marks": total_marks})



is_submitting_exam = False  # Flag to check if exam submission is already in progress

@app.route('/submit_exam', methods=['POST'])
@login_required
def submit_exam():
    global is_submitting_exam
    username = current_user.id
    exam_code = request.form.get('examCode')
    connection = sqlite3.connect("instance/data.db")
    cursor = connection.cursor()
    # Check if the exam submission is already in progress
    if is_submitting_exam:
        return jsonify({"message": "Exam submission is already in progress."})

    is_submitting_exam = True

    # Access the file data
    for file_name, file_data in request.files.items():
        # Get the original filename without the "_data" suffix
        original_file_name = file_name.split('_data')[0]
        blob = file_data.read()
        query = "INSERT INTO exam_submission (username, exam_code, answer) VALUES (?, ?, ?)"
        cursor.execute(query, (username, exam_code, blob))
        connection.commit()

    # Reset the flag after processing the exam submission
    is_submitting_exam = False

    return jsonify({"message": "Exam submitted!"})



@app.route('/marks')
@login_required
def marks():
    # Retrieve marks details from the database based on the username
    connection = sqlite3.connect("instance/data.db")
    cursor = connection.cursor()
    query = "SELECT exam_code, marks FROM marks WHERE username = ?"
    cursor.execute(query, (current_user.id,))
    marks_results = cursor.fetchall()

    marks_data = []
    for row in marks_results:
        exam_code, marks = row
        marks_data.append({'exam_code': exam_code, 'marks': marks})

    # Render the marks details template with marks data
    return render_template('marks.html', marks_data=marks_data)




@app.route('/quiz')
@login_required
def quiz():
    return render_template('quiz.html')


@app.route('/exam')
@login_required
def exam():
    return render_template('exam.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True)
