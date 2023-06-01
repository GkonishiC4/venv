from flask import Flask, render_template, request, redirect, url_for, flash,jsonify
from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms.validators import DataRequired, Email, EqualTo
from flask_mail import Mail, Message
from wtforms import PasswordField, SubmitField, validators


app = Flask(__name__)
app.config['SECRET_KEY'] = '5791628bb0b13ce0c676dfde280ba245'


# configuração do Flask-Mail para enviar e-mails
app.config['MAIL_SERVER']='smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'guilhemeappflow@gmail.com'
app.config['MAIL_PASSWORD'] = 'oghobneztdbikirt'
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_USE_TLS'] = False
mail = Mail(app)

# rota de index
@app.route('/')
def index():
    return render_template('index.html')

# rota de cadastro de usuário
class RegistrationForm(FlaskForm):
    email = StringField('E-mail', validators=[DataRequired(), Email()])
    password = PasswordField('Senha', validators=[DataRequired(message='insira uma senha'),
                                                  EqualTo('confirma', message='A confirmação de senha é inválida'),
                                                  validators.Length(min=8, message='A senha deve ter pelo menos 8 caracteres')])
    confirm_password = PasswordField('Confirmar Senha', validators=[DataRequired(message='insira uma senha'),
                                                  EqualTo('confirma', message='A confirmação de senha é inválida'),
                                                  validators.Length(min=8, message='A senha deve ter pelo menos 8 caracteres')])
    submit = SubmitField('Cadastrar')

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        flash('Cadastro bem-sucedido! Faça login para continuar.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

# rota de login de usuário
class LoginForm(FlaskForm):
    email = StringField('E-mail', validators=[DataRequired(), Email()])
    password = PasswordField('Senha', validators=[DataRequired()])
    submit = SubmitField('Entrar')

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        flash('Login bem-sucedido!', 'success')
        return redirect(url_for('index'))
    return render_template('login.html', form=form)

# rota de redefinição de senha
class ResetPasswordForm(FlaskForm):
    email = StringField('E-mail', validators=[DataRequired(), Email()])
    submit = SubmitField('Enviar E-mail para Redefinição')

@app.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user_email = form.email.data
        msg = Message('Redefinir Senha', sender='guilhemeappflow@gmail.com', recipients=[user_email])
        msg.body = f"Clique no seguinte link para redefinir sua senha: {url_for('reset_password_confirm', _external=True)}"
        mail.send(msg)
        flash('E-mail de redefinição de senha enviado!', 'success')
        return redirect(url_for('login'))
    return render_template('reset_password.html', form=form)

from flask import Flask, render_template, request, redirect, url_for, flash
import re

@app.route('/reset_password_confirm', methods=['GET', 'POST'])
def reset_password_confirm():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm-password']
        
        if password != confirm_password:
            flash('As senhas não coincidem.')
            return redirect(url_for('reset_password_confirm'))
        
        if not re.match(r'^(?=.*[A-Z])(?=.*[a-z])(?=.*[!@#$&*]).{8,}$', password):
            flash('A senha deve ter no mínimo 8 caracteres, sendo 1 maiúscula, 1 minúscula e 1 caractere especial.')
            return redirect(url_for('reset_password_confirm'))
        
        flash('Senha redefinida com sucesso.')
        return redirect(url_for('success'))
    
    return render_template('reset_password_confirm.html')

@app.route('/sobre')
def sobre():
    return render_template('sobre.html')

if __name__ == '__main__':
    app.run(debug=True)