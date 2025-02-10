from flask import Flask, jsonify, request
from main import app, con
import re
from flask_bcrypt import generate_password_hash, check_password_hash

@app.route('/livros', methods=['GET'])
def livros():
    cursor = con.cursor()
    cursor.execute("SELECT id_livro, titulo, autor, ano_publicacao FROM livros")
    livros = cursor.fetchall()
    livros_dic = []

    for livros in livros:
        livros_dic.append({
            'id_livro': livros[0],
            'titulo': livros[1],
            'autor':livros[2],
            'ano_publicacao':livros[3]
        })

    return jsonify(mensagem='Lista de Livros', livros=livros_dic)

@app.route('/livros', methods=['POST'])
def livro_post():
    data = request.get_json()
    titulo = data.get('titulo')
    autor = data.get('autor')
    ano_publicacao = data.get('ano_publicacao')

    cursor = con.cursor()

    cursor.execute('SELECT 1 FROM LIVROS WHERE TITULO = ?' , (titulo, ))

    if cursor.fetchone():
        return jsonify('Livro já cadastrado')

    cursor.execute("INSERT INTO LIVROS(TITULO, AUTOR, ANO_PUBLICACAO) values(?, ?, ?)",
                   (titulo, autor, ano_publicacao))

    con.commit()
    cursor.close()

    return jsonify({
        'message': "Livro cadastrado com sucesso!",
        'livro': {
            "titulo": titulo,
            "autor": autor,
            "ano_publicacao": ano_publicacao
        }
    })


@app.route('/livros/<int:id>', methods=['PUT'])
def livro_put(id):
    cursor = con.cursor()
    cursor.execute("select id_livro, titulo, autor, ano_publicacao from livros WHERE id_livro = ?", (id,))
    livro_data =  cursor.fetchone()

    if not livro_data:
        cursor.close()
        return jsonify({"error": "Livro não existe!"}),404

    data = request.get_json()
    titulo = data.get('titulo')
    autor = data.get('autor')
    ano_publicacao = data.get('ano_publicacao')


    cursor.execute("update livros set titulo = ?, autor = ?, ano_publicacao = ? where id_livro = ?",
                   (titulo, autor, ano_publicacao, id))

    con.commit()
    cursor.close()

    return jsonify({
        'menssage': 'Livro atualizado',
        'livro': {
            'id_livro': id,
            'titulo': titulo,
            'autor': autor,
            'ano_publicacao': ano_publicacao
        }
    })

@app.route('/livros/<int:id>', methods=['DELETE'])
def deletar_livro(id):
    cursor = con.cursor()

    cursor.execute("SELECT 1 FROM livros WHERE ID_LIVRO = ?", (id,))
    if not cursor.fetchone():
        cursor.close()
        return jsonify({"error": "Livro não encontrado"}), 404

    cursor.execute("DELETE FROM livros WHERE ID_LIVRO = ?", (id,))
    con.commit()
    cursor.close()

    return jsonify({
        'message': "Livro excluído com sucesso!",
        'id_livro': id
    })


def validar_senha (senha):
    if len(senha) < 8:
        return "A senha deve ter pelo menos 8 caracteres!"
    if not any(char.isupper() for char in senha):
        return "A senha deve ter pelo menos um caractere em maiúscula!"
    if not any(char.isdigit() for char in senha):
        return "A senha deve ter pelo menos um número!"
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", senha):
        return "A senha deve ter pelo menos um caractere especial!"

@app.route('/usuario', methods=['GET'])
def usuario():
    cursor = con.cursor()
    cursor.execute("SELECT id_usuario, nome, email, senha FROM usuario")
    usuario = cursor.fetchall()
    usuario_dic = []

    for usuario in usuario:
        usuario_dic.append({
            'id_usuario': usuario[0],
            'nome': usuario[1],
            'email': usuario[2],
            'senha': usuario[3]
        })

    return jsonify(mensagem='Lista de usuario!', usuario=usuario_dic)

@app.route('/usuario', methods=['POST'])
def usuario_post():
    data = request.get_json()
    nome = data.get('nome')
    email = data.get('email')
    senha = data.get('senha')

    cursor = con.cursor()

    cursor.execute('SELECT 1 FROM USUARIO WHERE NOME = ?', (nome, ))

    if cursor.fetchone():
        return jsonify('Usuario já cadastrado!')

    cursor.execute("INSERT INTO USUARIO(NOME, EMAIL, SENHA) values(?, ?, ?)",
                   (nome, email, senha))

    con.commit()
    cursor.close()

    return jsonify({
        'message': "Usuario cadastrado com sucesso!",
        'livro': {
            "nome": nome,
            "email": email,
            "senha": senha
        }
    })

@app.route('/usuario/<int:id>', methods=['PUT'])
def usuario_put(id):
    cursor = con.cursor()
    cursor.execute("select id_usuario, nome, email, senha FROM usuario WHERE id_usuario = ?", (id,))
    usuario_data = cursor.fetchone()

    if not usuario_data:
        cursor.close()
        return jsonify({"error": "Livro não existe!"}), 404

    data = request.get_json()
    nome = data.get('nome')
    email = data.get('email')
    senha = data.get('senha')

    cursor.execute("update usuario set nome = ?, email = ?, senha = ? where id_usuario = ?",
                   (nome, email, senha, id))

    con.commit()
    cursor.close()

    return jsonify({
        'message': 'Usuario atualizado!',
        'Usuario': {
            'id_usuario': id,
            'nome': nome,
            'email': email,
            'senha': senha
        }
    })

@app.route('/usuario/<int:id>', methods=['DELETE'])
def deletar_usuario(id):
    cursor = con.cursor()

    cursor.execute("SELECT 1 FROM usuario WHERE ID_USUARIO = ?", (id,))
    if not cursor.fetchone():
        cursor.close()
        return jsonify({"error": "Usuario não encontrado!"}), 404

    cursor.execute("DELETE FROM usuario WHERE ID_USUARIO = ?", (id, ))
    con.commit()
    cursor.close()

    return jsonify({
        'message': "Usuario excluído com sucesso!",
        'id_livro': id
    })

@app.route('/usuario/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    senha = data.get('senha')
    cursor = con.cursor()

    cursor.execute("SELECT senha FROM usuario WHERE email = ?", (email, ))
    senha = cursor.fetchone()
    cursor.close()

    if not senha:
        return jsonify({"error": "Usuário não encontrado!"}), 404

    senha_hash = senha[0]

    if check_password_hash(senha_hash, senha):
        return jsonify({"message": "Login efetuado com sucesso!"}), 200

    return jsonify({"error": "Email ou senha inválidos"}), 401


