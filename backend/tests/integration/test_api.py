from backend.tests.fakes import FakeAudioLLM


def test_health_reports_models(client):
    body = client.get("/api/v1/health").json()
    assert body["status"] == "ready"
    assert body["models"]["audio_llm"]["state"] == "ready"
    assert body["translation_available"] is True and body["diarization_available"] is True


def test_conversation(client, dialogue_wav):
    response = client.post("/api/v1/conversations/analyze", files={"audio": ("call.wav", dialogue_wav, "audio/wav")})
    assert response.status_code == 200, response.text
    body = response.json()

    assert set(body) == {"analysis", "diarization_info", "acoustic_features", "metadata", "turn_taking_metrics"}
    assert body["diarization_info"]["num_speakers"] == 2
    assert body["metadata"]["audio_filename"] == "call.wav"
    assert body["metadata"]["processing_timestamp"]
    assert body["analysis"]["conversation_analysis"]["duration_estimate"].endswith("seconds")
    assert body["analysis"]["prosody_analysis"]["quantitative_metrics"]["voice_quality"]["spectral_centroid_hz"] > 0


def test_conversation_prompt_includes_diarization_context(make_client, dialogue_wav):
    llm = FakeAudioLLM()
    client = make_client(audio_llm=llm)
    client.post("/api/v1/conversations/analyze", files={"audio": ("call.wav", dialogue_wav)})
    assert "Speaker diarization detected 2 speakers" in llm.calls[0][1]


def test_conversation_translated(client, dialogue_wav):
    body = client.post(
        "/api/v1/conversations/analyze", files={"audio": ("call.wav", dialogue_wav)}, data={"translate": "true"}
    ).json()
    assert set(body) == {"EN", "AR"}
    assert body["AR"]["analysis"]["conversation_analysis"]["overall_sentiment"] == "مختلط"


def test_translate_without_model_is_flagged(make_client, dialogue_wav):
    client = make_client()  # no text model
    assert client.get("/api/v1/health").json()["status"] == "degraded"
    body = client.post(
        "/api/v1/conversations/analyze", files={"audio": ("a.wav", dialogue_wav)}, data={"translate": "true"}
    ).json()
    assert body["metadata"]["translation"] == "unavailable"


def test_errors(make_client, client, dialogue_wav):
    assert client.post("/api/v1/conversations/analyze", files={"audio": ("a.wav", b"garbage")}).status_code == 422
    too_big = dialogue_wav + b"\0" * (1024 * 1024)
    assert client.post("/api/v1/conversations/analyze", files={"audio": ("a.wav", too_big)}).status_code == 413

    broken = make_client(fail_audio=True)
    assert broken.get("/api/v1/health").json()["status"] == "unavailable"
    assert broken.post("/api/v1/conversations/analyze", files={"audio": ("a.wav", dialogue_wav)}).status_code == 503


def test_root_points_to_docs_and_health(client):
    assert client.get("/").json()["health"] == "/api/v1/health"
