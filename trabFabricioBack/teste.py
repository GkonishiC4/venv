from flask import Flask, request, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import zipfile
import io
import json

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql://admin_erp:!fatec123@bd-trabalho-fabricio-fatecrp.postgres.database.azure.com/projeto_erp?sslmode=require"
db = SQLAlchemy(app)

# Definição dos modelos

class Usuario(db.Model):
    __tablename__ = 'tb_usuarios'
    
    id = db.Column(db.Integer, primary_key=True)
    login = db.Column(db.String(11), nullable=False)
    senha = db.Column(db.String(128), nullable=False)

    @property
    def senha(self):
        raise AttributeError('senha: campo somente para escrita')

    @senha.setter
    def senha(self, senha):
        if not self._verificar_requisitos_senha(senha):
            raise ValueError('A senha não atende aos requisitos mínimos.')
        self.senha = generate_password_hash(senha)

    def verificar_senha(self, senha):
        return check_password_hash(self.senha_hash, senha)

    def _verificar_requisitos_senha(self, senha):
        # Defina os requisitos mínimos para a senha
        comprimento_minimo = 8
        tem_letras_maiusculas = any(c.isupper() for c in senha)
        tem_letras_minusculas = any(c.islower() for c in senha)
        tem_digitos = any(c.isdigit() for c in senha)
        
        # Realize as verificações
        if len(senha) < comprimento_minimo:
            return False
        if not tem_letras_maiusculas:
            return False
        if not tem_letras_minusculas:
            return False
        if not tem_digitos:
            return False
        return True

class Cargo(db.Model):
    __tablename__ = 'tb_cargo'

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)

class StatusFuncionario(db.Model):
    __tablename__ = 'tb_status_funcionario'

    id = db.Column(db.Integer, primary_key=True)
    descricao = db.Column(db.String(100), nullable=False)

class Funcionario(db.Model):
    __tablename__ = 'tb_funcionario'

    id = db.Column(db.Integer,unique=True, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    sobrenome = db.Column(db.String)
    cpf = db.Column(db.String(11),unique=True,nullable=False)
    data_nascimento = db.Column(db.Date)
    email = db.Column(db.String)
    telefone = db.Column(db.String)

    cargo_id = db.Column(db.Integer, db.ForeignKey('tb_cargo.id'), nullable=False)
    cargo = db.relationship('Cargo', backref=db.backref('funcionarios', lazy=True))

    status_funcionario_id = db.Column(db.Integer, db.ForeignKey('tb_status_funcionario.id'), nullable=False)
    status_funcionario = db.relationship('StatusFuncionario', backref=db.backref('funcionarios', lazy=True))

# Cadastra um novo funcionário
@app.route('/cadastro/funcionarios', methods=['POST'])
def create_funcionario():
    data = request.get_json()
    novo_funcionario = Funcionario(
        nome=data['nome'],
        sobrenome=data['sobrenome'],
        cpf=data['cpf'],
        data_nascimento=datetime.strptime(data['data_nascimento'], '%Y-%m-%d').date(),
        email=data['email'],
        telefone=data['telefone'],
        cargo_id=data['cargo_id'],
        status_funcionario_id=data['status_funcionario_id']
    )
    db.session.add(novo_funcionario)

    # Gera um novo usuário de login para o funcionário
    novo_usuario = Usuario(
        login=data['cpf'],  # Usando o CPF como login
        senha=generate_password_hash(data['senha'])
    )
    novo_funcionario.usuario = novo_usuario  # Associa o usuário ao funcionário
    db.session.add(novo_usuario)
    
    db.session.commit()

    return jsonify({'message': 'Funcionário e usuário de login cadastrados com sucesso!'}), 201

# Obtém um usuário pelo CPF
@app.route('/usuarios/cpf', methods=['POST'])
def get_usuario_by_cpf():
    data = request.get_json()
    cpf = data['cpf']

    usuario = Usuario.query.filter_by(login=cpf).first()

    if usuario:
        return jsonify({
            'id': usuario.id,
            'login': usuario.login,
        })
    else:
        return jsonify({'message': 'Usuário não encontrado.'}), 404

# Atualiza um funcionario pelo CPF
@app.route('/funcionarios/cpf/<string:cpf>', methods=['PUT'])
def update_funcionario_by_cpf(cpf):
    funcionario = Funcionario.query.filter_by(cpf=cpf).first()
    if not funcionario:
        return jsonify({'message': 'Funcionário não encontrado'}), 404
    
    data = request.get_json()
    funcionario.email = data.get('email', funcionario.email)
    funcionario.telefone = data.get('telefone', funcionario.telefone)
    funcionario.cargo_id = data.get('cargo_id', funcionario.cargo_id)
    funcionario.status_funcionario_id = data.get('status_funcionario_id', funcionario.status_funcionario_id)
    
    db.session.commit()
    return jsonify({'message': 'Funcionário atualizado com sucesso!'}), 200

# Delete um funcionario pelo CPF
@app.route('/funcionarios/cpf/<string:cpf>', methods=['DELETE'])
def delete_funcionario_by_cpf(cpf):
    funcionario = Funcionario.query.filter_by(cpf=cpf).first()
    if not funcionario:
        return jsonify({'message': 'Funcionário não encontrado'}), 404
    
    db.session.delete(funcionario)
    db.session.commit()

    return jsonify({'message': 'Funcionário excluídos com sucesso!'}), 200

@app.route('/usuarios/<int:id>', methods=['DELETE'])
def delete_usuario_by_id(id):
    usuario = Usuario.query.get(id)
    if not usuario:
        return jsonify({'message': 'Usuário não encontrado'}), 404
    
    db.session.delete(usuario)
    db.session.commit()
    
    return jsonify({'message': 'Usuário excluído com sucesso!'}), 200

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    login = data.get('login')
    senha = data.get('senha')

    if not login or not senha:
        return jsonify({'message': 'Credenciais inválidas'}), 400

    usuario = Usuario.query.filter_by(login=login).first()

    if not usuario or not usuario.verificar_senha(senha):
        return jsonify({'message': 'Login ou senha inválidos'}), 401

    return jsonify({'message': 'Login realizado com sucesso'})

class Produto(db.Model):
    __tablename__ = 'tb_produto'

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    descricao = db.Column(db.String(255))
    preco = db.Column(db.Float, nullable=False)
    quantidade = db.Column(db.Integer)

@app.route('/produtos', methods=['GET'])
def get_produtos():
    produtos = Produto.query.all()
    resultado = []
    for produto in produtos:
        resultado.append({
            'id': produto.id,
            'nome': produto.nome,
            'descricao': produto.descricao,
            'preco': produto.preco
        })
    return jsonify(resultado), 200

@app.route('/produtos/<int:id>', methods=['GET'])
def get_produto(id):
    produto = Produto.query.get(id)
    if produto:
        return jsonify({
            'id': produto.id,
            'nome': produto.nome,
            'descricao': produto.descricao,
            'preco': produto.preco
        }), 200
    return jsonify({'message': 'Produto não encontrado'}), 404

@app.route('/produtos', methods=['POST'])
def create_produto():
    data = request.get_json()
    novo_produto = Produto(
        nome=data['nome'],
        descricao=data['descricao'],
        preco=data['preco']
    )
    db.session.add(novo_produto)
    db.session.commit()
    return jsonify({'message': 'Produto criado com sucesso!'}), 201

@app.route('/produtos/<int:id>', methods=['PUT'])
def update_produto(id):
    produto = Produto.query.get(id)
    if not produto:
        return jsonify({'message': 'Produto não encontrado'}), 404

    data = request.get_json()
    produto.nome = data['nome']
    produto.descricao = data['descricao']
    produto.preco = data['preco']
    db.session.commit()
    return jsonify({'message': 'Produto atualizado com sucesso!'}), 200

@app.route('/produtos/<int:id>', methods=['DELETE'])
def delete_produto(id):
    produto = Produto.query.get(id)
    if not produto:
        return jsonify({'message': 'Produto não encontrado'}), 404

    db.session.delete(produto)
    db.session.commit()
    return jsonify({'message': 'Produto excluído com sucesso!'}), 200

class Cliente(db.Model):
    __tablename__ = 'tb_cliente'

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    telefone = db.Column(db.String(20))
    cnpj = db.Column(db.String,unique=True, nullable=False)
    id_status_cliente = db.Column(db.Integer, db.ForeignKey('tb_status_funcionario.id_status_funcionario'))
    id_endereco = db.Column(db.Integer, db.ForeignKey('tb_endereco.id_endereco'))

def get_clientes():
    clientes = Cliente.query.all()
    resultado = []
    for cliente in clientes:
        resultado.append({
            'id': cliente.id,
            'nome': cliente.nome,
            'email': cliente.email,
            'telefone': cliente.telefone
        })
    return jsonify(resultado), 200

@app.route('/clientes/<int:id>', methods=['GET'])
def get_cliente(id):
    cliente = Cliente.query.get(id)
    if cliente:
        return jsonify({
            'id': cliente.id,
            'nome': cliente.nome,
            'email': cliente.email,
            'telefone': cliente.telefone
        }), 200
    return jsonify({'message': 'Cliente não encontrado'}), 404

@app.route('/clientes', methods=['POST'])
def create_cliente():
    data = request.get_json()
    novo_cliente = Cliente(
        nome=data['nome'],
        email=data['email'],
        telefone=data['telefone']
    )
    db.session.add(novo_cliente)
    db.session.commit()
    return jsonify({'message': 'Cliente criado com sucesso!'}), 201

@app.route('/clientes/<int:id>', methods=['PUT'])
def update_cliente(id):
    cliente = Cliente.query.get(id)
    if not cliente:
        return jsonify({'message': 'Cliente não encontrado'}), 404

    data = request.get_json()
    cliente.nome = data['nome']
    cliente.email = data['email']
    cliente.telefone = data['telefone']
    db.session.commit()
    return jsonify({'message': 'Cliente atualizado com sucesso!'}), 200

@app.route('/clientes/<int:id>', methods=['DELETE'])
def delete_cliente(id):
    cliente = Cliente.query.get(id)
    if not cliente:
        return jsonify({'message': 'Cliente não encontrado'}), 404

    db.session.delete(cliente)
    db.session.commit()
    return jsonify({'message': 'Cliente excluído com sucesso!'}), 200

class Venda(db.Model):
    __tablename__ = 'tb_venda'

    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey('tb_cliente.id'), nullable=False)
    produto_id = db.Column(db.Integer, db.ForeignKey('tb_produto.id'), nullable=False)
    quantidade = db.Column(db.Integer, nullable=False)
    valor_total = db.Column(db.Float, nullable=False)

@app.route('/vendas', methods=['GET'])
def get_vendas():
    vendas = Venda.query.all()
    resultado = []
    for venda in vendas:
        resultado.append({
            'id': venda.id,
            'cliente_id': venda.cliente_id,
            'produto_id': venda.produto_id,
            'quantidade': venda.quantidade,
            'valor_total': venda.valor_total
        })
    return jsonify(resultado), 200

@app.route('/vendas/<int:id>', methods=['GET'])
def get_venda(id):
    venda = Venda.query.get(id)
    if venda:
        return jsonify({
            'id': venda.id,
            'cliente_id': venda.cliente_id,
            'produto_id': venda.produto_id,
            'quantidade': venda.quantidade,
            'valor_total': venda.valor_total
        }), 200
    return jsonify({'message': 'Venda não encontrada'}), 404

@app.route('/vendas', methods=['POST'])
def create_venda():
    data = request.get_json()
    nova_venda = Venda(
        cliente_id=data['cliente_id'],
        produto_id=data['produto_id'],
        quantidade=data['quantidade'],
        valor_total=data['valor_total']
    )
    db.session.add(nova_venda)
    db.session.commit()
    return jsonify({'message': 'Venda criada com sucesso!'}), 201

@app.route('/vendas/<int:id>', methods=['PUT'])
def update_venda(id):
    venda = Venda.query.get(id)
    if not venda:
        return jsonify({'message': 'Venda não encontrada'}), 404

    data = request.get_json()
    venda.cliente_id = data['cliente_id']
    venda.produto_id = data['produto_id']
    venda.quantidade = data['quantidade']
    venda.valor_total = data['valor_total']
    db.session.commit()
    return jsonify({'message': 'Venda atualizada com sucesso!'}), 200

@app.route('/vendas/<int:id>', methods=['DELETE'])
def delete_venda(id):
    venda = Venda.query.get(id)
    if not venda:
        return jsonify({'message': 'Venda não encontrada'}), 404

    db.session.delete(venda)
    db.session.commit()
    return jsonify({'message': 'Venda excluída com sucesso!'}), 200

@app.route('/vendas/exportar', methods=['GET'])
def exportar_vendas():
    vendas = Venda.query.all()
    
    # Cria um arquivo zip em memória
    memory_file = io.BytesIO()
    with zipfile.ZipFile(memory_file, 'w') as zip_file:
        for venda in vendas:
            # Cria um arquivo com o ID da venda como nome dentro do arquivo zip
            nome_arquivo = f'venda_{venda.id}.txt'
            
            # Cria o conteúdo do arquivo
            conteudo_arquivo = f"Cliente ID: {venda.cliente_id}\nProduto ID: {venda.produto_id}\nQuantidade: {venda.quantidade}\nValor Total: {venda.valor_total}"
            
            # Adiciona o arquivo ao arquivo zip
            zip_file.writestr(nome_arquivo, conteudo_arquivo)
    
    # Move o cursor do arquivo zip para o início
    memory_file.seek(0)
    
    # Retorna o arquivo zip como uma resposta para o cliente
    return send_file(
        memory_file,
        mimetype='application/zip',
        as_attachment=True,
        attachment_filename='vendas.zip'
    )

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
