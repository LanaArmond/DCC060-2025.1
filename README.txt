# REQUISITOS
* Pyhton 3.10+
* MySQL (XAMPP)

# Instruções para Configuração do Ambiente Python

## Configuração do Ambiente Virtual e Instalação de Dependências

1. **Crie um ambiente virtual Python** (venv):  
   ```bash
   python -m venv venv
   ```

2. **Ative o ambiente virtual**:  
   - No Windows:  
     ```bash
     .\venv\Scripts\activate
     ```  
   - No Linux/MacOS:  
     ```bash
     source venv/bin/activate
     ```

3. **Instale as dependências do projeto** (arquivo `requirements.txt`):  
   ```bash
   pip install -r requirements.txt
   ```

---

## Comandos do Projeto

- **`python seeder.py`**  
  Reseta e popula o banco de dados com dados iniciais (seeding).  

- **`python tests.py`**  
  Reseta o banco de dados, executa o seeding e testa a maior parte da funcionalidade do sistema.  

- **`python indexes_load_test.py`**  
  Sobrecarrega os modelos relevantes (cursos e usuários) para testar a performance dos índices no banco de dados.  

- **`python main.py`**  
  Inicia o aplicativo Flask principal. **Execute somente após rodar o seeder (`seeder.py`)**.  

---

## Configuração do Arquivo `.env`

O arquivo `.env` é **obrigatório** para o funcionamento do projeto. Todas as chaves necessárias estão no arquivo `.envexample`.  

### Passos:  
1. Copie o arquivo `.envexample` e renomeie para `.env`.  
2. Preencha as variáveis no arquivo `.env`:  
   - `SECRET_KEY`: Uma chave secreta para a aplicação Flask.  
   - `DATABASE_URL`: URL de conexão com o banco de dados no formato:  
     ```ini
     DATABASE_URL=mysql+mysqlconnector://root:@localhost/test
     ```  
     (Substitua `root`, `localhost` e `test` conforme sua configuração do MySQL.)  

---

**Observação**: Certifique-se de que o MySQL está rodando localmente antes de executar os scripts.  
```