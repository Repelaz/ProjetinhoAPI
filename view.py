from flask import Flask, jsonify, request, send_file
from main import app, con
import re
from flask_bcrypt import generate_password_hash, check_password_hash
import jwt
from fpdf import FPDF
import os
import tempfile

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

app.config.from_pyfile("config.py")

SECRET_KEY = app.config['SECRET_KEY']

def generate_token(user_id):
    payload = {'id_usuario': user_id}
    token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
    return token

@app.route('/livros/relatorio', methods=['GET'])
def livro_relatorio():
    cursor = con.cursor()
    cursor.execute("SELECT id_livro, titulo, autor, ano_publicacao FROM livros")
    livros = cursor.fetchall()
    cursor.close()

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", style='B', size=16)
    pdf.cell(200, 10, "Relatório de Livros", ln=True, align='C')

    pdf.ln(5)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)

    pdf.set_font("Arial", size=12)
    for livro in livros:
        pdf.cell(200, 10, f"ID: {livro[0]} - {livro[1]} - {livro[2]} - {livro[3]}", ln=True)

    contador_livros = len(livros)
    pdf.ln(10)
    pdf.set_font("Arial", style='B', size=12)
    pdf.cell(200, 10, f"Total de livros cadastrados: {contador_livros}", ln=True, align='C')

    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    pdf.output(temp_file.name)
    temp_file.close()

    return send_file(temp_file.name, as_attachment=True, mimetype='application/pdf')

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    senha = data.get('senha')
    cursor = con.cursor()
    cursor.execute("SELECT senha, id_usuario FROM usuario WHERE email = ?", (email,))
    resultado = cursor.fetchone()
    cursor.close()

    if not resultado:
        return jsonify({"error": "Usuário não encontrado"}), 404

    senha_hash = resultado[0]
    id_usuario = resultado[1]

    if check_password_hash(senha_hash, senha):
        token = generate_token(id_usuario)
        return jsonify({'mensagem': 'Login com sucesso', 'token': token}), 200
    else:
        return jsonify({'mensagem': 'Email ou senha inválidos'}), 401

@app.route('/livros', methods=['GET'])
def livros():
    cursor = con.cursor()
    cursor.execute("SELECT id_livro, titulo, autor, ano_publicacao FROM livros")
    livros_lista = cursor.fetchall()
    cursor.close()

    livros_dic = []
    for livro in livros_lista:
        livros_dic.append({
            'id_livro': livro[0],
            'titulo': livro[1],
            'autor': livro[2],
            'ano_publicacao': livro[3]
        })

    return jsonify(mensagem='Lista de Livros', livros=livros_dic)

@app.route('/livros', methods=['POST'])
def livro_post():
    token = request.headers.get('Authorization')
    imagem = request.files.get('imagem')

    if not token:
        return jsonify({'mensagem': 'Token de autenticação necessário'}), 401

    token = remover_bearer(token)
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
    except jwt.ExpiredSignatureError:
        return jsonify({'mensagem': 'Token expirado'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'mensagem': 'Token inválido'}), 401


    data = request.get_json()
    titulo = data.get('titulo')
    autor = data.get('autor')
    ano_publicacao = data.get('ano_publicacao')

    cursor = con.cursor()
    cursor.execute('SELECT 1 FROM livros WHERE titulo = ?', (titulo,))
    if cursor.fetchone():
        cursor.close()
        return jsonify({'mensagem': 'Livro já cadastrado'}), 400

    cursor.execute("INSERT INTO livros(titulo, autor, ano_publicacao) values(?, ?, ?)", (titulo, autor, ano_publicacao))
    con.commit()
    cursor.close()

    return jsonify({'mensagem': "Livro cadastrado com sucesso!"})

@app.route('/livros/<int:id>', methods=['PUT'])
def livro_put(id):
    cursor = con.cursor()
    cursor.execute("SELECT id_livro FROM livros WHERE id_livro = ?", (id,))
    if not cursor.fetchone():
        cursor.close()
        return jsonify({"error": "Livro não existe!"}), 404

    data = request.get_json()
    titulo = data.get('titulo')
    autor = data.get('autor')
    ano_publicacao = data.get('ano_publicacao')

    cursor.execute("UPDATE livros SET titulo = ?, autor = ?, ano_publicacao = ? WHERE id_livro = ?", (titulo, autor, ano_publicacao, id))
    con.commit()
    cursor.close()

    return jsonify({'mensagem': 'Livro atualizado com sucesso!'})

@app.route('/usuario', methods=['POST'])
def usuario_post():
    data = request.get_json()
    nome = data.get('nome')
    email = data.get('email')
    senha = data.get('senha')

    cursor = con.cursor()
    cursor.execute("SELECT 1 FROM usuario WHERE email = ?", (email,))
    if cursor.fetchone():
        cursor.close()
        return jsonify({'error': 'Usuário já cadastrado!'}), 400

    senha_hash = generate_password_hash(senha).decode('utf-8')

    cursor.execute("INSERT INTO usuario(nome, email, senha) VALUES (?, ?, ?)", (nome, email, senha_hash))
    con.commit()
    cursor.close()

    return jsonify({'mensagem': "Usuário cadastrado com sucesso!"})

@app.route('/usuario/<int:id>', methods=['PUT'])
def usuario_put(id):
    cursor = con.cursor()
    cursor.execute("SELECT id_usuario FROM usuario WHERE id_usuario = ?", (id,))
    if not cursor.fetchone():
        cursor.close()
        return jsonify({"error": "Usuário não existe!"}), 404

    data = request.get_json()
    nome = data.get('nome')
    email = data.get('email')
    senha = data.get('senha')

    senha_hash = generate_password_hash(senha).decode('utf-8')

    cursor.execute("UPDATE usuario SET nome = ?, email = ?, senha = ? WHERE id_usuario = ?", (nome, email, senha_hash, id))
    con.commit()
    cursor.close()

    return jsonify({'mensagem': 'Usuário atualizado com sucesso!'})

@app.route('/usuario/<int:id>', methods=['DELETE'])
def deletar_usuario(id):
    cursor = con.cursor()
    cursor.execute("SELECT 1 FROM usuario WHERE id_usuario = ?", (id,))
    if not cursor.fetchone():
        cursor.close()
        return jsonify({"error": "Usuário não encontrado!"}), 404

    cursor.execute("DELETE FROM usuario WHERE id_usuario = ?", (id,))
    con.commit()
    cursor.close()

    return jsonify({'mensagem': "Usuário excluído com sucesso!"})

@app.route('/livros/imagem', methods=['POST'])
def livro_imagem():
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({'mensagem': 'Token de autenticação necessário'}), 401

    token = remover_bearer(token)
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        id_usuario = payload['id_usuario']
    except jwt.ExpiredSignatureError:
        return jsonify({'mensagem': 'Token expirado'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'mensagem': 'Token inválido'}), 401

    titulo = request.form.get('titulo')
    autor = request.form.get('autor')
    ano_publicacao = request.form.get('ano_publicacao')
    imagem = request.files.get('imagem')  # Arquivo enviado

    cursor = con.cursor()

    cursor.execute("SELECT 1 FROM livros WHERE TITULO = ?", (titulo,))
    if cursor.fetchone():
        cursor.close()
        return jsonify({"error": "Livro já cadastrado"}), 400

    cursor.execute(
        "INSERT INTO livros (TITULO, AUTOR, ANO_PUBLICACAO) VALUES (?, ?, ?) RETURNING ID_livro",
        (titulo, autor, ano_publicacao)
    )
    livro_id = cursor.fetchone()[0]
    con.commit()

    imagem_path = None
    if imagem:
        nome_imagem = f"{livro_id}.jpeg"  # Define o nome fixo com .jpeg
        pasta_destino = os.path.join(app.config['UPLOAD_FOLDER'], "Livros")
        os.makedirs(pasta_destino, exist_ok=True)
        imagem_path = os.path.join(pasta_destino, nome_imagem)
        imagem.save(imagem_path)


    cursor.close()

    return jsonify({
        'message': "Livro cadastrado com sucesso!",
        'livro': {
            'id': livro_id,
            'titulo': titulo,
            'autor': autor,
            'ano_publicacao': ano_publicacao,
            'imagem_path': imagem_path
        }
    }), 201

def remover_bearer(token):
    return token.replace('Bearer ', '') if token.startswith('Bearer ') else token
