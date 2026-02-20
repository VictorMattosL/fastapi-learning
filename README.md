# 🚀 API de Gerenciamento de Produtos (FastAPI)

Este é um projeto completo de Backend desenvolvido em Python utilizando **FastAPI**. A aplicação consiste em uma API RESTful para gerenciamento de produtos e usuários, com banco de dados relacional e autenticação segura.

🌐 **Acesse a API ao vivo:** [Documentação Interativa (Swagger)](https://fastapi-learning-m1iw.onrender.com/docs)

---

## 🛠️ Tecnologias Utilizadas

- **FastAPI:** Framework web principal, rápido e moderno.
- **SQLAlchemy:** ORM (Object-Relational Mapping) para comunicação com o banco de dados.
- **SQLite:** Banco de dados relacional leve.
- **Pydantic:** Validação e serialização de dados.
- **Passlib & Argon2:** Hashing de senhas seguro.
- **PyJWT:** Geração e validação de tokens JWT para autenticação.
- **Uvicorn:** Servidor ASGI para rodar a aplicação.
- **Render:** Plataforma de Deploy na nuvem.

---

## ⚙️ Funcionalidades da API

A API está dividida em três módulos principais:

### 👤 1. Autenticação (`/auth`)
- **POST `/auth/token`**: Recebe `username` e `password`, valida no banco de dados e retorna um Token JWT válido por tempo determinado.

### 👥 2. Usuários (`/users`)
- **POST `/users/`**: Cria um novo usuário com senha criptografada.
- **GET `/users/`**: Lista todos os usuários cadastrados (sem retornar as senhas).
- **GET `/users/{user_id}`**: Busca um usuário específico pelo ID.

### 📦 3. Produtos (`/products`)
- **POST `/products/`**: Cria um novo produto. *(Requer Autenticação JWT)* 🔒
- **GET `/products/`**: Lista todos os produtos ou filtra por preço mínimo/máximo.
- **GET `/products/{product_id}`**: Busca os detalhes de um produto específico.
- **PUT `/products/{product_id}`**: Atualiza os dados de um produto existente.
- **DELETE `/products/{product_id}`**: Remove um produto do banco de dados.

---

## 💻 Como rodar localmente

Se quiser rodar o projeto na sua máquina, siga os passos abaixo:

1. Clone este repositório:
```bash
git clone https://github.com/VictorMattosL/fastapi-learning.git
