from datetime import datetime
from functools import wraps
import io
import logging
import os
import tempfile

from flask import Flask, request
from pydub import AudioSegment
from pydub.exceptions import CouldntDecodeError
import speech_recognition as sr

app = Flask(__name__)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

max_content_length_mb = int(os.getenv("MAX_CONTENT_LENGTH_MB", "50"))
app.config["MAX_CONTENT_LENGTH"] = max_content_length_mb * 1024 * 1024

raw_ips = os.getenv("ALLOWED_IPS", "").strip()
ALLOWED_IPS = {ip.strip() for ip in raw_ips.split(",") if ip.strip()} if raw_ips else None

logging.info("IPs permitidos: %s", ALLOWED_IPS if ALLOWED_IPS else "Todos")

SUPPORTED_CONTENT_TYPES = {
    "audio/wav": "wav",
    "audio/wave": "wav",
    "audio/x-wav": "wav",
    "audio/ogg": "ogg",
    "audio/mp3": "mp3",
    "audio/mpeg": "mp3",
    "audio/mp4": "m4a",
    "audio/m4a": "m4a",
    "audio/x-m4a": "m4a",
}

SUPPORTED_EXTENSIONS = {
    ".wav": "wav",
    ".ogg": "ogg",
    ".mp3": "mp3",
    ".m4a": "m4a",
    ".mp4": "m4a",
}


def request_client_ip():
    forwarded_for = request.headers.get("X-Forwarded-For", "")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.remote_addr


def check_ip(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        request_ip = request_client_ip()

        if ALLOWED_IPS is not None and request_ip not in ALLOWED_IPS:
            logging.warning("Tentativa de acesso nao autorizada do IP: %s", request_ip)
            return {"erro": "Acesso nao autorizado"}, 403

        return f(*args, **kwargs)

    return decorated_function


def detect_audio_format(file_storage=None):
    if file_storage:
        content_type = (file_storage.content_type or "").lower()
        if content_type in SUPPORTED_CONTENT_TYPES:
            return SUPPORTED_CONTENT_TYPES[content_type]

        _, extension = os.path.splitext(file_storage.filename or "")
        extension = extension.lower()
        if extension in SUPPORTED_EXTENSIONS:
            return SUPPORTED_EXTENSIONS[extension]

    request_content_type = (request.content_type or "").split(";")[0].lower()
    return SUPPORTED_CONTENT_TYPES.get(request_content_type)


def detect_audio_format_from_bytes(audio_bytes):
    if audio_bytes.startswith(b"RIFF") and audio_bytes[8:12] == b"WAVE":
        return "wav"
    if audio_bytes.startswith(b"OggS"):
        return "ogg"
    if audio_bytes.startswith(b"ID3") or audio_bytes[:2] in (b"\xff\xfb", b"\xff\xf3", b"\xff\xf2"):
        return "mp3"
    if len(audio_bytes) > 12 and audio_bytes[4:8] == b"ftyp":
        return "m4a"
    return None


def read_audio_from_request():
    file_storage = request.files.get("audio") or request.files.get("file")

    if file_storage:
        audio_bytes = file_storage.read()
        audio_format = detect_audio_format(file_storage)
    else:
        audio_bytes = request.get_data()
        audio_format = detect_audio_format()

    if not audio_bytes:
        return None, None

    detected_format = detect_audio_format_from_bytes(audio_bytes)
    if detected_format:
        audio_format = detected_format

    return audio_bytes, audio_format


def to_wav_io(audio_bytes, audio_format):
    if audio_format == "wav":
        return io.BytesIO(audio_bytes)

    input_path = None
    output_path = None

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{audio_format}") as input_file:
            input_file.write(audio_bytes)
            input_path = input_file.name

        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as output_file:
            output_path = output_file.name

        try:
            audio = AudioSegment.from_file(input_path)
        except CouldntDecodeError:
            audio = AudioSegment.from_file(input_path, format=audio_format)
        audio = audio.set_frame_rate(16000).set_channels(1)
        audio.export(output_path, format="wav")

        with open(output_path, "rb") as wav_file:
            return io.BytesIO(wav_file.read())
    finally:
        for path in (input_path, output_path):
            if path and os.path.exists(path):
                os.remove(path)


@app.before_request
def log_request_info():
    logging.info("Request IP: %s", request_client_ip())
    logging.info("Content-Type: %s", request.content_type)


@app.route("/", methods=["GET"])
@check_ip
def home():
    return {
        "status": "ok",
        "endpoints": {
            "health": "/health",
            "transcrever": 'POST /transcrever com arquivo multipart nos campos "audio" ou "file"',
        },
    }


@app.route("/health", methods=["GET"])
def health():
    return {"status": "ok"}, 200


@app.route("/transcrever", methods=["POST"])
@check_ip
def transcrever():
    request_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    request_ip = request_client_ip()

    logging.info("Requisicao recebida do IP: %s", request_ip)

    audio_bytes, audio_format = read_audio_from_request()
    if not audio_bytes:
        logging.error("%s - Nenhum arquivo de audio enviado - IP: %s", request_time, request_ip)
        return {"erro": "Nenhum arquivo de audio enviado"}, 400

    if audio_format not in {"wav", "ogg", "mp3", "m4a"}:
        logging.error("%s - Tipo de arquivo nao suportado - IP: %s", request_time, request_ip)
        return {"erro": "Apenas arquivos WAV, OGG, MP3 e M4A sao permitidos"}, 400

    try:
        wav_io = to_wav_io(audio_bytes, audio_format)

        recognizer = sr.Recognizer()
        with sr.AudioFile(wav_io) as source:
            audio_data = recognizer.record(source)

        transcribed_text = recognizer.recognize_google(audio_data, language="pt-BR")

        logging.info("%s - Transcricao bem-sucedida - IP: %s", request_time, request_ip)
        return transcribed_text, 200

    except sr.UnknownValueError:
        logging.error("%s - Nao foi possivel reconhecer o audio - IP: %s", request_time, request_ip)
        return {"erro": "Nao foi possivel reconhecer o audio"}, 400
    except sr.RequestError as e:
        logging.error(
            "%s - Erro ao se comunicar com o servico de reconhecimento de fala: %s - IP: %s",
            request_time,
            e,
            request_ip,
        )
        return {"erro": "Erro ao se comunicar com o servico de reconhecimento de fala"}, 500
    except CouldntDecodeError:
        logging.exception("%s - Nao foi possivel decodificar o audio - IP: %s", request_time, request_ip)
        return {"erro": "Nao foi possivel decodificar o audio enviado"}, 400
    except Exception as e:
        logging.exception("%s - Erro inesperado: %s - IP: %s", request_time, e, request_ip)
        return {"erro": "Erro interno no servidor"}, 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")))
