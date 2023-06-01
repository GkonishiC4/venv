from flask import Flask, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
import re
from flask_mail import Mail
import requests
from bd import *
from flask_cors import CORS
import secrets
import string

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

class Usuario(db.Model):
    __tablename__ = 'tb_usuario'
    
    id = db.Column(db.Integer, primary_key=True)
    login = db.Column(db.String(11), nullable=False)
    senha = db.Column(db.String(128), nullable=False)
    primeiro_acesso = db.Column(db.Boolean, nullable=False, default=True)

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
    
    caracteres = string.ascii_letters + string.digits + string.punctuation
    senha_aleatoria = ''.join(secrets.choice(caracteres) for _ in range(12))

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
    novoUsuario = Usuario(login=cpf, senha=senha_aleatoria, primeiro_acesso=True)
    db.session.add(novoUsuario)
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

@app.route("/redefinir-senha", methods=["POST"])
def redefinir_senha():
    data = request.get_json()
    cpf = data["cpf"]
    nova_senha = data["nova_senha"]

    usuario = Usuario.query.filter_by(login=cpf, primeiro_acesso=True).first()

    if not usuario:
        return jsonify({
            "message": "Usuário não encontrado ou já realizou a redefinição de senha.",
            "statusCode": 404
        }), 404


    usuario.primeiro_acesso = False
    usuario.senha = nova_senha
    db.session.commit()

    return jsonify({
        "message": "Senha redefinida com sucesso.",
        "statusCode": 200
    }), 200

@app.route("/deletar-funcionario/<string:email>", methods=["DELETE"])
def deletar_funcionario(email):
    funcionario = Funcionario.query.filter_by(email=email).first()

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
    cpf = data["cpf"]
    senha = data["senha"]

    usuario = Usuario.query.filter_by(login=cpf).first()

    if not usuario:
        return jsonify({
            "message": "Usuário não encontrado.",
            "statusCode": 404
        }), 404

    if usuario.primeiro_acesso:
        return jsonify({
            "message": "É necessário redefinir a senha antes de fazer o login.",
            "statusCode": 401
        }), 401


    return jsonify({
        "message": "Login bem-sucedido!",
        "statusCode": 200
    }), 200


@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    cpf = data["cpf"]
    senha = data["senha"]

    usuario = Usuario.query.filter_by(login=cpf).first()

    if not usuario or not check_password_hash(senha, senha):
        return jsonify({
            "message": "Credenciais inválidas.",
            "statusCode": 401
        }), 401

    return jsonify({
        "message": "Login bem-sucedido!",
        "cpf":cpf,
        "statusCode": 200
    }), 200
 

@app.route("/funcionario/<int:funcionario_id>", methods=["PUT"])
def update_funcionario(funcionario_id):
    data = request.get_json()
    nome = data.get('nome')
    sobrenome = data.get('sobrenome')
    cpf = data.get('cpf')
    data_nascimento = data.get('data_nascimento')
    email = data.get('email')
    telefone = data.get('telefone')

    funcionario = Funcionario.query.get(funcionario_id)

    if not funcionario:
        return jsonify({
            "message": "Funcionário não encontrado.",
            "statusCode": 404
        }), 404

    if nome:
        funcionario.nome = nome
    if sobrenome:
        funcionario.sobrenome = sobrenome
    if cpf:
        funcionario.cpf = cpf
    if data_nascimento:
        funcionario.data_nascimento = data_nascimento
    if email:
        funcionario.email = email
    if telefone:
        funcionario.telefone = telefone

    try:
        db.session.commit()
        return jsonify({
            "message": "Dados do funcionário atualizados com sucesso.",
            "statusCode": 200
        }), 200

    except Exception as error:
        print(error)
        return jsonify({
            "message": "Por algum motivo não conseguimos atualizar os dados do funcionário.",
            "statusCode": 500
        }), 500


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

