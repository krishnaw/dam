import json
import subprocess


class VideoService:
    @staticmethod
    def get_video_info(file_path: str) -> dict:
        """Get video metadata using ffprobe."""
        cmd = [
            "ffprobe", "-v", "quiet", "-print_format", "json",
            "-show_format", "-show_streams", file_path,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        data = json.loads(result.stdout)

        video_stream = next(
            (s for s in data.get("streams", []) if s["codec_type"] == "video"), None
        )
        audio_stream = next(
            (s for s in data.get("streams", []) if s["codec_type"] == "audio"), None
        )

        fps = None
        if video_stream:
            frame_rate = video_stream.get("r_frame_rate", "0/1")
            parts = frame_rate.split("/")
            if len(parts) == 2 and int(parts[1]) != 0:
                fps = int(parts[0]) / int(parts[1])
            else:
                fps = float(parts[0]) if parts[0] != "0" else None

        return {
            "duration": float(data["format"].get("duration", 0)),
            "width": int(video_stream["width"]) if video_stream else None,
            "height": int(video_stream["height"]) if video_stream else None,
            "codec": video_stream.get("codec_name") if video_stream else None,
            "fps": fps,
            "bitrate": int(data["format"].get("bit_rate", 0)),
            "has_audio": audio_stream is not None,
            "file_size": int(data["format"].get("size", 0)),
        }

    @staticmethod
    def transcode(
        input_path: str,
        output_path: str,
        codec: str = "libx264",
        resolution: str | None = None,
        bitrate: str | None = None,
        preset: str = "medium",
    ) -> str:
        """Transcode video file."""
        cmd = ["ffmpeg", "-i", input_path, "-c:v", codec, "-preset", preset]

        if resolution:
            w, h = resolution.split("x")
            cmd.extend([
                "-vf",
                f"scale={w}:{h}:force_original_aspect_ratio=decrease,"
                f"pad={w}:{h}:(ow-iw)/2:(oh-ih)/2",
            ])

        if bitrate:
            cmd.extend(["-b:v", bitrate])

        cmd.extend(["-c:a", "aac", "-b:a", "128k"])
        cmd.extend(["-movflags", "+faststart"])
        cmd.extend(["-y", output_path])

        subprocess.run(cmd, check=True, capture_output=True)
        return output_path

    @staticmethod
    def extract_thumbnail(input_path: str, timestamp: float = 1.0) -> bytes:
        """Extract a frame from video at given timestamp."""
        cmd = [
            "ffmpeg", "-ss", str(timestamp), "-i", input_path,
            "-vframes", "1", "-f", "image2", "-c:v", "mjpeg", "pipe:1",
        ]
        result = subprocess.run(cmd, capture_output=True, check=True)
        return result.stdout

    @staticmethod
    def extract_audio(
        input_path: str, output_path: str, audio_format: str = "mp3"
    ) -> str:
        """Extract audio track from video."""
        cmd = ["ffmpeg", "-i", input_path, "-vn", "-c:a"]
        if audio_format == "mp3":
            cmd.extend(["libmp3lame", "-q:a", "2"])
        else:
            cmd.append("copy")
        cmd.extend(["-y", output_path])
        subprocess.run(cmd, check=True, capture_output=True)
        return output_path

    @staticmethod
    def generate_preview_clip(
        input_path: str, output_path: str, duration: float = 10.0
    ) -> str:
        """Generate a short preview clip from the video."""
        cmd = [
            "ffmpeg", "-i", input_path, "-t", str(duration),
            "-c:v", "libx264", "-preset", "fast", "-crf", "28",
            "-c:a", "aac", "-b:a", "96k",
            "-movflags", "+faststart", "-y", output_path,
        ]
        subprocess.run(cmd, check=True, capture_output=True)
        return output_path
