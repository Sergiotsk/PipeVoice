"""Tests for Transcriber._is_hallucination() and transcribe() discard behavior.

Cada test está etiquetado con el escenario de la spec que cubre —
ver openspec/specs/hallucination-filtering/spec.md (local, no versionado
en el repo público, ver docs/06-operaciones/BACKLOG.md).
"""

import numpy as np
import pytest

from pipevoice.transcriber import Transcriber


@pytest.fixture
def transcriber():
    """Transcriber sin cargar el modelo real (constructor es liviano)."""
    return Transcriber(model_name="tiny")


class TestKnownHallucinationPhrases:
    """Requirement: Detección de frases de alucinación conocidas."""

    def test_short_known_phrase_is_discarded(self, transcriber):
        """Scenario: Silencio produce alucinación de cierre de video."""
        assert transcriber._is_hallucination("Gracias por ver el video.") is True

    def test_long_real_speech_with_known_word_is_not_discarded(self, transcriber):
        """Scenario: Habla real similar a una frase de la lista no se
        descarta por longitud — el texto limpio tiene 30+ caracteres."""
        text = "Gracias, dale que después seguimos hablando de este tema"
        assert len(text.strip(".,")) >= 30
        assert transcriber._is_hallucination(text) is False

    def test_japanese_closing_phrase_is_discarded(self, transcriber):
        """Frase de alucinación conocida en japonés, del bug real reportado."""
        assert transcriber._is_hallucination("お疲れ様でした") is True


class TestRepeatedCharacterLoop:
    """Requirement: Detección de loops de caracteres repetidos."""

    def test_long_low_variety_string_is_discarded(self, transcriber):
        """Scenario: Glitch de loop de caracteres en silencio prolongado."""
        glitch = "xyzxyzxyzxyzxyzxyz"  # 18 chars, solo 3 únicos
        assert len(glitch) > 15
        assert transcriber._is_hallucination(glitch) is True

    def test_short_real_word_does_not_trigger_loop_filter(self, transcriber):
        """Scenario: Texto real corto no dispara el filtro de loop."""
        assert transcriber._is_hallucination("hola") is False

    def test_long_varied_real_sentence_is_not_discarded(self, transcriber):
        """Texto largo con suficiente variedad de caracteres no es un loop."""
        text = "El pescado que compré ayer en el mercado estaba buenísimo"
        assert transcriber._is_hallucination(text) is False


class TestEdgeCases:
    def test_empty_string_is_not_a_hallucination(self, transcriber):
        assert transcriber._is_hallucination("") is False


class TestTranscribeDiscardsHallucination:
    """Requirement: Transparencia del descarte."""

    def test_transcribe_returns_empty_and_logs_on_hallucination(
        self, transcriber, monkeypatch, capsys
    ):
        """Scenario: Log visible al descartar."""

        class FakeModel:
            def transcribe(self, audio, **options):
                return {"text": "gracias por ver el video"}

        monkeypatch.setattr(transcriber, "_model", FakeModel())

        result = transcriber.transcribe(np.ones(16000, dtype=np.float32))

        assert result == ""
        captured = capsys.readouterr()
        assert "Ignored hallucination" in captured.err
        assert captured.out == ""  # nunca se emite basura a stdout

    def test_transcribe_returns_real_text_unmodified(
        self, transcriber, monkeypatch
    ):
        class FakeModel:
            def transcribe(self, audio, **options):
                return {"text": "  hola, cómo va  "}

        monkeypatch.setattr(transcriber, "_model", FakeModel())

        result = transcriber.transcribe(np.ones(16000, dtype=np.float32))

        assert result == "hola, cómo va"
