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
- `API_TOKEN`: token obrigatorio usado para proteger os endpoints `/` e `/transcrever`.
- `MAX_CONTENT_LENGTH_MB`: tamanho maximo do upload em MB. Padrao: `2048`.
- `WORKERS`: quantidade de workers do Gunicorn. Padrao: `16`.
- `THREADS`: threads por worker. Padrao: `2`.
- `TIMEOUT`: timeout de cada request em segundos. Padrao: `3600`.
- `GRACEFUL_TIMEOUT`: tempo para shutdown gracioso dos workers. Padrao: `300`.
- `KEEP_ALIVE`: keep-alive HTTP do Gunicorn. Padrao: `5`.
- `MAX_REQUESTS`: reinicia workers depois desta quantidade de requests. Padrao: `1000`.
- `MAX_REQUESTS_JITTER`: variacao aleatoria do `MAX_REQUESTS`. Padrao: `100`.
- `WORKER_TMP_DIR`: diretorio temporario dos workers Gunicorn. Padrao: `/dev/shm`.
- `TMPFS_SIZE`: tamanho do `/tmp` em memoria para conversoes do ffmpeg. Padrao: `8G`.
- `SHM_SIZE`: tamanho de `/dev/shm`. Padrao: `2G`.
- `MEMORY_LIMIT`: limite de memoria no compose. Padrao: `48G`.
- `MEMORY_RESERVATION`: reserva de memoria no compose. Padrao: `16G`.
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

Aceita arquivos WAV, OGG, MP3 e M4A.

Envie o token configurado em `API_TOKEN` no header
`Authorization: Bearer seu-token` ou `X-API-Token: seu-token`.

Envio multipart usando o campo `audio`:

```bash
curl -X POST \
  -H "Authorization: Bearer seu-token" \
  -F "audio=@/path/to/audio.wav" \
  http://localhost:5000/transcrever
```

Tambem aceita o campo `file`:

```bash
curl -X POST \
  -H "Authorization: Bearer seu-token" \
  -F "file=@/path/to/audio.mp3" \
  http://localhost:5000/transcrever
```

Ou envio do audio como corpo bruto da requisicao:

```bash
curl -X POST \
  -H "Authorization: Bearer seu-token" \
  -H "Content-Type: audio/wav" \
  --data-binary "@/path/to/audio.wav" \
  http://localhost:5000/transcrever
```

Resposta de sucesso em texto puro:

```text
texto transcrito
```
