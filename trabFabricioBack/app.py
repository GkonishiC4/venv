from flask import Flask, request, jsonify,send_file
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
import re
from flask_mail import Mail, Message
import zipfile
import os
import json
import requests
from bd import *
from flask_cors import CORS
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql://admin_erp:!fatec123@bd-trabalho-fabricio-fatecrp.postgres.database.azure.com/projeto_erp?sslmode=require"
db = SQLAlchemy(app)

app.config['MAIL_SERVER']='smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'guilhemeappflow@gmail.com'
app.config['MAIL_PASSWORD'] = 'oghobneztdbikirt'
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_USE_TLS'] = False
mail = Mail(app)


def validate_password(password):
    #mínimo 8 caracteres.
    if len(password) < 8:
        return False
    #mínimo 1 letra minuscula
    if not re.search(r"[a-z]", password):
        return False
    #mínimo 1 letra maiuscula
    if not re.search(r"[A-Z]", password):
        return False
    #mínimo 1 número
    if not re.search(r"\d", password):
        return False
    return True

class Cargo(db.Model):
    _tablename_ = 'tb_cargo'

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)

class StatusFuncionario(db.Model):
    _tablename_ = 'tb_status_funcionario'
    
    id = db.Column(db.Integer, primary_key=True)
    descricao = db.Column(db.String(100), nullable=False)

class Funcionario(db.Model):
    _tablename_ = 'tb_funcionario'

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    sobrenome = db.Column(db.String)
    cpf = db.Column(db.String(11))
    data_nascimento = db.Column(db.Date)
    email = db.Column(db.String)
    telefone = db.Column(db.String)

    cargo_id = db.Column(db.Integer, db.ForeignKey('cargo.id'), nullable=False)
    cargo = db.relationship('Cargo', backref=db.backref('funcionarios', lazy=True))

    status_funcionario_id = db.Column(db.Integer, db.ForeignKey('status_funcionario.id'), nullable=False)
    status_funcionario = db.relationship('StatusFuncionario', backref=db.backref('funcionarios', lazy=True))


@app.route('/')
def index():
    return 'Hello, world!'

@app.route("/cadastrar", methods=["POST"])
def cadastrar():
    data = request.get_json()

    cpf = data['cpf']
    
    if Funcionario.query.filter_by(cpf=cpf).first():
        return jsonify({
            "message": "CPF já cadastrado.",
            "statusCode": 400
        }), 400
    
    if len(cpf) != 11:
        return jsonify({
            "message": "CPF deve conter exatamente 11 dígitos.",
            "statusCode": 400
        }), 400

    nome = data['nome']
    sobrenome = data['sobrenome']
    cpf = data['cpf']
    data_nascimento = data['data_nascimento']
    email = data['email']
    telefone = data['telefone']
    status_funcionario_id = data['status_funcionario_id']
    cargo_id = data['cargo_id']

    novoFuncionario = Funcionario(
        nome=nome,
        sobrenome=sobrenome,
        cpf=cpf,
        data_nascimento=data_nascimento,
        email=email,
        telefone=telefone,
        status_funcionario_id=status_funcionario_id,
        cargo_id=cargo_id
    )

    db.session.add(novoFuncionario)

    try:
        db.session.commit()
        return jsonify({
            "message": "Cadastro bem-sucedido!",
            "statusCode": 201
        }), 201

    except Exception as error:
        print(error)
        return jsonify({
            "message": "Por algum motivo não conseguimos fazer o cadastro do usuário.",
            "statusCode": 500
        }), 500

@app.route("/funcionarios/delete/<str:funcionario_cpf>", methods=["DELETE"])
def deletar_funcionario(funcionario_cpf):
    funcionario = Funcionario.query.get(funcionario_cpf)

    if not funcionario:
        return jsonify({
            "message": "Funcionário não encontrado.",
            "statusCode": 404
        }), 404

    db.session.delete(funcionario)
    db.session.commit()

    return jsonify({
        "message": "Funcionário deletado com sucesso.",
        "statusCode": 200
    }), 200

@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    username = data["username"]
    password = data["password"]

    user = Funcionario.query.filter_by(username=username).first()
    if not user or not check_password_hash(password, password):
        return jsonify({
            "message": "Credenciais inválidas.",
            "statusCode": 401
        }), 401

    return jsonify({
        "message": "Login bem-sucedido!",
        "username":username,
        "statusCode": 200
    }), 200
 
@app.route("/reset-password", methods=["POST"])
def reset_password():
    data = request.get_json()
    email = data["email"]

    user = Funcionario.query.filter_by(email=email).first()
    if not user:
        return jsonify({
            "message": "O e-mail fornecido não está cadastrado.",
            "statusCode": 404
        }), 404

    token = generate_password_hash(email)

    msg = Message("Redefinição de senha", sender="seu-email@example.com", recipients=[email])
    msg.body = f"Para redefinir sua senha, acesse o link: http://seusite.com/reset-password/{token}"
    mail.send(msg)

    return jsonify({
        "message": "Um e-mail de redefinição de senha foi enviado para o endereço fornecido.",
        "statusCode": 200
    }), 200

@app.route("/delete", methods=["DELETE"])
def delete_user_by_email():
    data = request.get_json()
    email = data["email"]

    user = Funcionario.query.filter_by(email=email).first()

    if not user:
        return jsonify({
            "message": "Usuário não encontrado.",
            "statusCode": 404
        }), 404

    db.session.delete(user)
    db.session.commit()

    return jsonify({
        "message": "Usuário deletado com sucesso.",
        "statusCode": 200
    }), 200

@app.route("/usuario/atualizar", methods=["PUT"])
def atualizar_usuario_email():

    data = request.get_json()
    email = data["email"]

    usuarios = Funcionario.query.filter_by(email=email).first()

    if not usuarios:
        return jsonify({
            "message": "Usuário não encontrado.",
            "statusCode": 404
        }), 404

    if "nome" in data:
        nome = data["nome"]
    if "email" in data:
        email = data["email"]
    if "senha" in data:
        senha = data["senha"]
    if "cargo" in data:
        cargo = data["cargo"]
    

        if not validate_password(senha):
            return jsonify({
                "message": "A senha deve ter no mínimo 8 caracteres e conter pelo menos uma letra maiúscula, uma letra minúscula e um dígito numérico.",
                "statusCode": 400
            }), 400
        
        hashed_password = generate_password_hash(senha)
        senha = hashed_password

    db.session.commit()

    return jsonify({
        "message": "Informações do usuário atualizadas com sucesso.",
        "statusCode": 200
    }), 200

@app.route("/export-users", methods=["GET"])
def export_users():
    users = Funcionario.query.all()
    users_data = []

    for user in users:
        user_data = {
            "id": id,
            "username": username,
            "email": email,
        }
        users_data.append(user_data)

    json_filename = "users.json"
    with open(json_filename, "w") as json_file:
        json.dump(users_data, json_file)

    zip_filename = "export.zip"
    table_name = Funcionario.__tablename__
    export_folder = os.path.join(app.root_path, "export")
    zip_path = os.path.join(export_folder, zip_filename)

    with zipfile.ZipFile(zip_path, "w") as zip_file:
        zip_file.write(json_filename, f"{table_name}.json")

    os.remove(json_filename)

    return send_file(zip_path, mimetype="application/zip", as_attachment=True, attachment_filename=zip_filename)

@app.route('/endereco', methods=['POST'])
def obter_endereco():
    data = request.get_json()
    cep = data['cep']
    numero = data['numero']

    
    url = f'https://viacep.com.br/ws/{cep}/json/'
    response = requests.get(url)

    if response.status_code == 200:
        endereco_via_cep = response.json()

        return jsonify({
            'mensagem': 'Endereço obtido e salvo com sucesso.',
            'status': 'sucesso',
            'endereco': endereco_via_cep
        }), 200
    else:
        return jsonify({
            'mensagem': 'Não foi possível obter o endereço.',
            'status': 'erro'
        }), 500
    
@app.route('/endereco/<int:endereco_id>', methods=['DELETE'])
def delete_endereco(endereco_id):
    endereco = Endereco.query.get(endereco_id)

    if not endereco:
        return jsonify({'message': 'Endereço não encontrado.'}), 404

    db.session.delete(endereco)
    db.session.commit()

    return jsonify({'message': 'Endereço excluído com sucesso.'})

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        app.run(debug= True)
