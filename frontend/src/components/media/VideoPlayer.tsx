import { useState, useRef, useEffect } from "react";
import {
  Play,
  Pause,
  Volume2,
  VolumeX,
  Maximize,
  ChevronDown,
} from "lucide-react";
import { Button } from "@/components/ui/button";

interface VideoPlayerProps {
  src: string;
  poster?: string;
}

function formatTime(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${m}:${s.toString().padStart(2, "0")}`;
}

const speeds = [0.5, 1, 1.5, 2];

export function VideoPlayer({ src, poster }: VideoPlayerProps) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const [playing, setPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [volume, setVolume] = useState(1);
  const [muted, setMuted] = useState(false);
  const [speed, setSpeed] = useState(1);
  const [showSpeedMenu, setShowSpeedMenu] = useState(false);

  useEffect(() => {
    const vid = videoRef.current;
    if (!vid) return;
    const onTime = () => setCurrentTime(vid.currentTime);
    const onDuration = () => setDuration(vid.duration);
    const onEnded = () => setPlaying(false);
    vid.addEventListener("timeupdate", onTime);
    vid.addEventListener("loadedmetadata", onDuration);
    vid.addEventListener("ended", onEnded);
    return () => {
      vid.removeEventListener("timeupdate", onTime);
      vid.removeEventListener("loadedmetadata", onDuration);
      vid.removeEventListener("ended", onEnded);
    };
  }, []);

  const togglePlay = () => {
    const vid = videoRef.current;
    if (!vid) return;
    if (playing) {
      vid.pause();
    } else {
      vid.play();
    }
    setPlaying(!playing);
  };

  const handleSeek = (e: React.ChangeEvent<HTMLInputElement>) => {
    const vid = videoRef.current;
    if (!vid) return;
    const time = Number(e.target.value);
    vid.currentTime = time;
    setCurrentTime(time);
  };

  const handleVolume = (e: React.ChangeEvent<HTMLInputElement>) => {
    const vid = videoRef.current;
    if (!vid) return;
    const v = Number(e.target.value);
    vid.volume = v;
    setVolume(v);
    setMuted(v === 0);
  };

  const toggleMute = () => {
    const vid = videoRef.current;
    if (!vid) return;
    vid.muted = !muted;
    setMuted(!muted);
  };

  const handleSpeed = (s: number) => {
    const vid = videoRef.current;
    if (!vid) return;
    vid.playbackRate = s;
    setSpeed(s);
    setShowSpeedMenu(false);
  };

  const handleFullscreen = () => {
    videoRef.current?.requestFullscreen();
  };

  return (
    <div className="group relative w-full overflow-hidden rounded-lg bg-black">
      <video
        ref={videoRef}
        src={src}
        poster={poster ?? undefined}
        className="w-full"
        onClick={togglePlay}
      />

      <div className="absolute inset-x-0 bottom-0 bg-gradient-to-t from-black/80 to-transparent p-3 opacity-0 transition-opacity group-hover:opacity-100">
        <input
          type="range"
          min={0}
          max={duration || 0}
          step={0.1}
          value={currentTime}
          onChange={handleSeek}
          className="mb-2 h-1 w-full cursor-pointer accent-primary"
        />

        <div className="flex items-center gap-2">
          <Button
            variant="ghost"
            size="icon"
            className="h-7 w-7 text-white hover:text-white"
            onClick={togglePlay}
          >
            {playing ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
          </Button>

          <span className="text-xs text-white/80">
            {formatTime(currentTime)} / {formatTime(duration)}
          </span>

          <div className="ml-auto flex items-center gap-2">
            <Button
              variant="ghost"
              size="icon"
              className="h-7 w-7 text-white hover:text-white"
              onClick={toggleMute}
            >
              {muted ? <VolumeX className="h-4 w-4" /> : <Volume2 className="h-4 w-4" />}
            </Button>
            <input
              type="range"
              min={0}
              max={1}
              step={0.05}
              value={muted ? 0 : volume}
              onChange={handleVolume}
              className="h-1 w-16 cursor-pointer accent-primary"
            />

            <div className="relative">
              <Button
                variant="ghost"
                size="sm"
                className="h-7 gap-1 px-2 text-xs text-white hover:text-white"
                onClick={() => setShowSpeedMenu(!showSpeedMenu)}
              >
                {speed}x
                <ChevronDown className="h-3 w-3" />
              </Button>
              {showSpeedMenu && (
                <div className="absolute bottom-full right-0 mb-1 rounded-md border bg-popover p-1 shadow-lg">
                  {speeds.map((s) => (
                    <button
                      key={s}
                      onClick={() => handleSpeed(s)}
                      className={`block w-full rounded px-3 py-1 text-left text-xs hover:bg-muted ${
                        s === speed ? "font-bold text-primary" : ""
                      }`}
                    >
                      {s}x
                    </button>
                  ))}
                </div>
              )}
            </div>

            <Button
              variant="ghost"
              size="icon"
              className="h-7 w-7 text-white hover:text-white"
              onClick={handleFullscreen}
            >
              <Maximize className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
