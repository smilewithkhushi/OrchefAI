import riva.client
from config import NVIDIA_API_KEY

RIVA_ASR_URI = "grpc.nvcf.nvidia.com:443"
PARAKEET_FUNCTION_ID = "1598d209-5e27-4d3c-8079-4751568b1081"


def transcribe_audio(audio_bytes: bytes, language: str = "en-US") -> str:
    auth = riva.client.Auth(
        use_ssl=True,
        uri=RIVA_ASR_URI,
        metadata_args=[
            ["function-id", PARAKEET_FUNCTION_ID],
            ["authorization", f"Bearer {NVIDIA_API_KEY}"],
        ],
    )

    asr_service = riva.client.ASRService(auth)

    config = riva.client.RecognitionConfig()
    config.encoding = riva.client.AudioEncoding.LINEAR_PCM
    config.sample_rate_hertz = 16000
    config.language_code = language
    config.max_alternatives = 1
    config.enable_automatic_punctuation = True
    config.audio_channel_count = 1

    # Use streaming for a single chunk since offline_recognize
    # doesn't support this model's parameters
    responses = list(asr_service.streaming_response_generator(
        audio_chunks=[audio_bytes],
        streaming_config=riva.client.StreamingRecognitionConfig(config=config),
    ))

    for resp in responses:
        for result in resp.results:
            if result.is_final and result.alternatives:
                return result.alternatives[0].transcript.strip()
    return ""
