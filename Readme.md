# API de transcricao de audio para texto

API Flask simples que recebe audio por requisicao HTTP e usa `SpeechRecognition`
para transcrever em portugues do Brasil.

Atencao: este projeto usa a biblioteca `SpeechRecognition`, que se comunica com
o servico publico do Google para fazer as transcricoes.

## Deploy no Coolify

Use o deploy por Docker Compose. O arquivo `docker-compose.yaml` nao publica uma
porta fixa no host; ele apenas expoe a porta interna do container para o proxy do
Coolify.

Variaveis uteis:

- `PORT`: porta interna usada pelo Gunicorn. Padrao: `5000`.
- `ALLOWED_IPS`: lista opcional de IPs separados por virgula.
- `MAX_CONTENT_LENGTH_MB`: tamanho maximo do upload em MB. Padrao: `50`.
- `WORKERS`: quantidade de workers do Gunicorn. Padrao: `4`.
- `LOGLEVEL`: nivel de log do Gunicorn. Padrao: `info`.

No Coolify, configure o dominio apontando para a porta interna `5000`, ou altere
`PORT` se quiser usar outra porta interna.

## Executar com Docker localmente

```bash
docker compose up --build
```

Para acessar localmente sem Coolify, publique uma porta manualmente:

```bash
docker run --rm -p 5000:5000 transcreve-api:latest
```

## Executar sem Docker

Instale as dependencias:

```bash
pip install -r requirements.txt
```

Tambem instale o `ffmpeg` no sistema.

Depois execute:

```bash
python main.py
```

## Endpoints

### `GET /health`

Retorna o status da API.

### `POST /transcrever`

Aceita arquivos WAV, OGG e MP3.

Envio multipart usando o campo `audio`:

```bash
curl -X POST -F "audio=@/path/to/audio.wav" http://localhost:5000/transcrever
```

Tambem aceita o campo `file`:

```bash
curl -X POST -F "file=@/path/to/audio.mp3" http://localhost:5000/transcrever
```

Ou envio do audio como corpo bruto da requisicao:

```bash
curl -X POST \
  -H "Content-Type: audio/wav" \
  --data-binary "@/path/to/audio.wav" \
  http://localhost:5000/transcrever
```

Resposta de sucesso em texto puro:

```text
texto transcrito
```
