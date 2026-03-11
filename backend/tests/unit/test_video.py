"""Unit tests for video service (subprocess mocked)."""

import json
from unittest.mock import MagicMock, patch

import pytest

from app.services.video import VideoService


@pytest.fixture
def ffprobe_output():
    """Sample ffprobe JSON output."""
    return json.dumps({
        "streams": [
            {
                "codec_type": "video",
                "codec_name": "h264",
                "width": 1920,
                "height": 1080,
                "r_frame_rate": "30/1",
            },
            {
                "codec_type": "audio",
                "codec_name": "aac",
            },
        ],
        "format": {
            "duration": "120.5",
            "bit_rate": "5000000",
            "size": "75000000",
        },
    })


class TestGetVideoInfo:
    @patch("app.services.video.subprocess.run")
    def test_parses_ffprobe_output(self, mock_run, ffprobe_output):
        mock_run.return_value = MagicMock(stdout=ffprobe_output)

        info = VideoService.get_video_info("/tmp/test.mp4")

        assert info["duration"] == 120.5
        assert info["width"] == 1920
        assert info["height"] == 1080
        assert info["codec"] == "h264"
        assert info["fps"] == 30.0
        assert info["bitrate"] == 5000000
        assert info["has_audio"] is True
        assert info["file_size"] == 75000000

    @patch("app.services.video.subprocess.run")
    def test_no_audio_stream(self, mock_run):
        data = json.dumps({
            "streams": [
                {"codec_type": "video", "codec_name": "h264", "width": 640, "height": 480, "r_frame_rate": "24/1"},
            ],
            "format": {"duration": "10", "bit_rate": "1000000", "size": "1000000"},
        })
        mock_run.return_value = MagicMock(stdout=data)

        info = VideoService.get_video_info("/tmp/test.mp4")
        assert info["has_audio"] is False

    @patch("app.services.video.subprocess.run")
    def test_calls_ffprobe_with_correct_args(self, mock_run, ffprobe_output):
        mock_run.return_value = MagicMock(stdout=ffprobe_output)

        VideoService.get_video_info("/tmp/video.mp4")

        args = mock_run.call_args[0][0]
        assert args[0] == "ffprobe"
        assert "-show_format" in args
        assert "-show_streams" in args
        assert "/tmp/video.mp4" in args


class TestTranscode:
    @patch("app.services.video.subprocess.run")
    def test_basic_transcode_command(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)

        VideoService.transcode("/tmp/input.mp4", "/tmp/output.mp4")

        args = mock_run.call_args[0][0]
        assert args[0] == "ffmpeg"
        assert "-i" in args
        assert "/tmp/input.mp4" in args
        assert "-c:v" in args
        assert "libx264" in args
        assert "/tmp/output.mp4" in args

    @patch("app.services.video.subprocess.run")
    def test_transcode_with_resolution(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)

        VideoService.transcode("/tmp/in.mp4", "/tmp/out.mp4", resolution="1280x720")

        args = mock_run.call_args[0][0]
        assert "-vf" in args
        vf_idx = args.index("-vf")
        assert "1280" in args[vf_idx + 1]
        assert "720" in args[vf_idx + 1]

    @patch("app.services.video.subprocess.run")
    def test_transcode_with_bitrate(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)

        VideoService.transcode("/tmp/in.mp4", "/tmp/out.mp4", bitrate="2M")

        args = mock_run.call_args[0][0]
        assert "-b:v" in args
        bv_idx = args.index("-b:v")
        assert args[bv_idx + 1] == "2M"

    @patch("app.services.video.subprocess.run")
    def test_transcode_includes_faststart(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)

        VideoService.transcode("/tmp/in.mp4", "/tmp/out.mp4")

        args = mock_run.call_args[0][0]
        assert "-movflags" in args
        assert "+faststart" in args


class TestExtractThumbnail:
    @patch("app.services.video.subprocess.run")
    def test_returns_stdout_bytes(self, mock_run):
        fake_jpeg = b"\xff\xd8\xff\xe0fake-jpeg-data"
        mock_run.return_value = MagicMock(stdout=fake_jpeg, returncode=0)

        result = VideoService.extract_thumbnail("/tmp/video.mp4", timestamp=2.5)

        assert result == fake_jpeg

    @patch("app.services.video.subprocess.run")
    def test_uses_correct_timestamp(self, mock_run):
        mock_run.return_value = MagicMock(stdout=b"data", returncode=0)

        VideoService.extract_thumbnail("/tmp/video.mp4", timestamp=5.0)

        args = mock_run.call_args[0][0]
        assert "-ss" in args
        ss_idx = args.index("-ss")
        assert args[ss_idx + 1] == "5.0"


class TestExtractAudio:
    @patch("app.services.video.subprocess.run")
    def test_extract_mp3(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)

        result = VideoService.extract_audio("/tmp/video.mp4", "/tmp/audio.mp3", "mp3")

        assert result == "/tmp/audio.mp3"
        args = mock_run.call_args[0][0]
        assert "libmp3lame" in args
        assert "-vn" in args

    @patch("app.services.video.subprocess.run")
    def test_extract_copy_codec(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)

        VideoService.extract_audio("/tmp/video.mp4", "/tmp/audio.aac", "aac")

        args = mock_run.call_args[0][0]
        assert "copy" in args
