from flask import Flask, render_template, flash, redirect, url_for, session, request, logging
#from data import employees
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from functools import wraps

app = Flask(__name__)

# Config MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'myflaskapp'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
# init MYSQL
mysql = MySQL(app)

#employees = employees()

# Index
@app.route('/')
def index():
    return render_template('home.html')


# About
@app.route('/about')
def about():
    return render_template('about.html')


# employees
@app.route('/employees')
def employees():
    # Create cursor
    cur = mysql.connection.cursor()

    # Get employees
    result = cur.execute("SELECT * FROM employees")

    employees = cur.fetchall()

    if result > 0:
        return render_template('employees.html', employees=employees)
    else:
        msg = ''
        # msg = 'No Employee is added'
        return render_template('employees.html', msg=msg)
    # Close connection
    cur.close()


#Single employee
@app.route('/employee/<string:id>/')
def employee(id):
    # Create cursor
    cur = mysql.connection.cursor()

    # Get employee
    result = cur.execute("SELECT * FROM employees WHERE id = %s", [id])

    employee = cur.fetchone()

    return render_template('employee.html', employee=employee)


# Register Form Class
class RegisterForm(Form):
    name = StringField('Name', [validators.Length(min=1, max=50)])
    username = StringField('Username', [validators.Length(min=4, max=25)])
    email = StringField('Email', [validators.Length(min=6, max=50)])
    password = PasswordField('Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Passwords do not match')
    ])
    confirm = PasswordField('Confirm Password')





# User login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Get Form Fields
        username = request.form['username']
        password_candidate = request.form['password']

        # Create cursor
        cur = mysql.connection.cursor()

        # Get user by username
        result = cur.execute("SELECT * FROM users WHERE username = %s", [username])

        if result > 0:
            # Get stored hash
            data = cur.fetchone()
            password = data['password']

            # Compare Passwords
            if sha256_crypt.verify(password_candidate, password):
                # Passed
                session['logged_in'] = True
                session['username'] = username

                flash('You are now logged in', 'success')
                return redirect(url_for('dashboard'))
            else:
                error = 'Invalid login'
                return render_template('login.html', error=error)
            # Close connection
            cur.close()
        else:
            error = 'Username not found'
            return render_template('login.html', error=error)

    return render_template('login.html')

# Check if user logged in
def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized, Please login', 'danger')
            return redirect(url_for('login'))
    return wrap

# Logout
@app.route('/logout')
@is_logged_in
def logout():
    session.clear()
    flash('You are now logged out', 'success')
    return redirect(url_for('login'))


# User Register
@app.route('/register', methods=['GET', 'POST'])
@is_logged_in
def register():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        name = form.name.data
        email = form.email.data
        username = form.username.data
        password = sha256_crypt.encrypt(str(form.password.data))

        # Create cursor
        cur = mysql.connection.cursor()

        # Execute query
        cur.execute("INSERT INTO users(name, email, username, password) VALUES(%s, %s, %s, %s)", (name, email, username, password))

        # Commit to DB
        mysql.connection.commit()

        # Close connection
        cur.close()

        flash('Face Mask Monitoring Team Officer is Added.', 'success')

        return redirect(url_for('login'))
    return render_template('register.html', form=form)


# Dashboard
@app.route('/dashboard')
@is_logged_in
def dashboard():
    # Create cursor
    cur = mysql.connection.cursor()

    # Get employees
    #result = cur.execute("SELECT * FROM employees")
    # Show employees only from the user logged in 
    result = cur.execute("SELECT * FROM employees  " ) #,  [session['username']]) 

    employees = cur.fetchall()

    if result > 0:
        return render_template('dashboard.html', employees=employees)
    else:
        msg = 'No Employee is added'
        return render_template('dashboard.html', msg=msg)
    # Close connection
    cur.close()

# employee Form Class
class employeeForm(Form):
    name = StringField('Name', [validators.Length(min=1, max=50), validators.required()])
    sex = StringField('Sex', [validators.Length(min=1, max=5)])
    department = StringField('Department', [validators.Length(min=1, max=50)])
    phone_no = StringField('Phone No', [validators.Length(min=9, max=12)])
    email = StringField('Email', [validators.Length(min=7, max=50), validators.required()])
    photo = TextAreaField('photo')
# Add employee
@app.route('/add_employee', methods=['GET', 'POST'])
@is_logged_in
def add_employee():
    form = employeeForm(request.form)
    if request.method == 'POST' and form.validate():
        name = form.name.data
        sex = form.sex.data
        department = form.department.data
        phone_no = form.phone_no.data
        email = form.email.data
        photo = form.photo.data
        # Create Cursor
        cur = mysql.connection.cursor()

        # Execute
        cur.execute("INSERT INTO employees(name, sex, department,  phone_no, email, photo) VALUES(%s, %s, %s, %s, %s, %s)",(name, sex, department, phone_no, email, session['username']))

        # Commit to DB
        mysql.connection.commit()

        #Close connection
        cur.close()

        flash("Employee's information is added.", 'success')

        return redirect(url_for('dashboard'))

    return render_template('add_employee.html', form=form)


# Edit employee
@app.route('/edit_employee/<string:id>', methods=['GET', 'POST'])
@is_logged_in
def edit_employee(id):
    # Create cursor
    cur = mysql.connection.cursor()

    # Get employee by id
    result = cur.execute("SELECT * FROM employees WHERE id = %s", [id])

    employee = cur.fetchone()
    cur.close()
    # Get form
    form = employeeForm(request.form)

    # Populate employee form fields
    form.name.data = employee['name']
    form.sex.data = employee['sex']
    form.department.data = employee['department']
    form.phone_no.data = employee['phone_no']
    form.email.data = employee['email']
    form.photo.data = employee['photo']
  
    if request.method == 'POST' and form.validate():
        name = request.form['name']
        sex = request.form['sex']
        department = request.form['department']
        phone_no = request.form['phone_no']
        email = request.form['email']
        photo = request.form['photo']

        # Create Cursor
        cur = mysql.connection.cursor()
        app.logger.info(name)
        # Execute
        cur.execute ("UPDATE employees SET name=%s, sex=%s, department=%s, phone_no=%s, email=%s, photo=%s WHERE id=%s",(name, sex, department, phone_no, email, photo, id))
        # Commit to DB
        mysql.connection.commit()

        #Close connection
        cur.close()

        flash('employee Updated', 'success')

        return redirect(url_for('dashboard'))

    return render_template('edit_employee.html', form=form)

# Delete employee
@app.route('/delete_employee/<string:id>', methods=['POST'])
@is_logged_in
def delete_employee(id):
    # Create cursor
    cur = mysql.connection.cursor()

    # Execute
    cur.execute("DELETE FROM employees WHERE id = %s", [id])

    # Commit to DB
    mysql.connection.commit()

    #Close connection
    cur.close()

    flash('employee Deleted', 'success')

    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    app.secret_key='secret123'
    app.run(debug=True)
    # port = int(os.environ.get("PORT", 33507))
    # app.run(host='0.0.0.0', debug=True, port=port)

