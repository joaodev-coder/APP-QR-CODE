# APP QR code

Aplicacao para transferir arquivos do celular para o computador via navegador.

## Para que serve

- Enviar arquivos para o PC sem cabo.
- Abrir uma pagina web no celular para selecionar e enviar.
- Salvar automaticamente em `uploads/`.
- Opcionalmente proteger envio com senha.

## Funcionalidades

- Servidor local com FastAPI.
- QR Code no terminal com URL de acesso.
- Upload em streaming (chunks).
- Modo `private` com token.
- Modo `public` sem senha.
- Interface responsiva com preview para imagens (arquivo unico ou varios).
- Mensagem final de envio concluido.
- Opcional: link publico temporario com Cloudflare Tunnel.

## Estrutura

```text
APP QR code/
|-- main.py
|-- static/
|   `-- index.html
|-- uploads/
|-- requirements.txt
|-- .env.example
`-- README.md
```

## Requisitos

- Python 3.10+
- Windows PowerShell
- Celular e computador com navegador

## Instalacao

1. Entre na pasta do projeto:

```powershell
cd "C:\caminho\para\APP QR code"
```

2. Crie o ambiente virtual:

```powershell
python -m venv .venv
```

3. Instale as dependencias:

```powershell
.\.venv\Scripts\pip.exe install -r requirements.txt
```

## Configuracao

1. Crie o arquivo `.env`:

```powershell
Copy-Item .env.example .env
```

2. Edite o `.env`:

```env
APP_MODE=private
UPLOAD_TOKEN=troque-esta-senha-para-uma-senha-forte
ALLOW_FILE_OVERWRITE=false
```

Significado:

- `APP_MODE=private`: exige senha.
- `APP_MODE=public`: sem senha.
- `UPLOAD_TOKEN`: senha usada no modo private.
- `ALLOW_FILE_OVERWRITE=false`: se arquivo com mesmo nome ja existir, o sistema cria nome unico automaticamente.
- `ALLOW_FILE_OVERWRITE=true`: sobrescreve arquivo com mesmo nome.

## Executar

```powershell
.\.venv\Scripts\python.exe main.py
```

Ao iniciar, o terminal mostra:

- QR Code.
- URL local (exemplo: `http://192.168.0.10:8000`).
- Modo ativo (`private` ou `public`).

## Como usar no celular

1. Abra a URL mostrada no terminal ou escaneie o QR Code.
2. Se estiver em `private`, informe a senha.
3. Selecione um ou varios arquivos.
4. Para imagens, o preview aparece antes do envio.
5. Clique em **Enviar**.
6. Ao concluir, aparece a mensagem:
   `Fotos enviadas com sucesso. Abra a pasta uploads no seu computador.`
7. Arquivos recebidos ficam em `uploads/`.

## Acesso fora da rede local (opcional)

1. Terminal A (servidor):

```powershell
.\.venv\Scripts\python.exe main.py
```

2. Terminal B (Cloudflare Tunnel):

```powershell
cloudflared tunnel --url http://localhost:8000
```

3. Abra no celular a URL `https://...trycloudflare.com` exibida no terminal do `cloudflared`.

Observacoes:

- O link muda a cada reinicio do tunnel.
- O link so funciona enquanto servidor e tunnel estiverem rodando.
- Para evitar acesso indevido, use `APP_MODE=private`.

## Publicar no GitHub com seguranca

- Nao commitar `.env`.
- Nao commitar arquivos pessoais dentro de `uploads/`.
- Commite apenas `.env.example` com valores de exemplo.

## Comandos uteis

Iniciar servidor:

```powershell
.\.venv\Scripts\python.exe main.py
```

Parar servidor/tunnel:

```text
Ctrl + C
```

## Problemas comuns

`Erro de porta em uso (10048)`
- Outra aplicacao ja esta usando a porta 8000.

`401 Token invalido`
- Senha informada no celular diferente de `UPLOAD_TOKEN`.

`Modo private ativo, mas UPLOAD_TOKEN nao foi definido`
- Falta criar ou preencher o arquivo `.env`.

`cloudflared: comando nao reconhecido`
- Instale o Cloudflared e abra um novo terminal.