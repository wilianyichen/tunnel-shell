"""Session recorder for TunnelShell.

Records PTY sessions for audit and replay.
"""

import json
import os
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional, List
from datetime import datetime


@dataclass
class RecordingEvent:
    """A single recording event."""
    timestamp: float
    event_type: str  # 'input', 'output', 'resize'
    data: str
    delay: float = 0.0  # Delay from previous event (for replay)


@dataclass
class RecordingMetadata:
    """Recording metadata."""
    session_id: str
    session_name: Optional[str]
    host: str
    start_time: float
    end_time: Optional[float] = None
    duration: float = 0.0
    event_count: int = 0
    file_size: int = 0
    
    def to_dict(self) -> dict:
        return asdict(self)


class SessionRecorder:
    """Records PTY session for replay."""
    
    def __init__(
        self,
        session_id: str,
        session_name: Optional[str] = None,
        host: str = "",
        output_dir: Optional[Path] = None,
    ):
        self.session_id = session_id
        self.session_name = session_name
        self.host = host
        self.output_dir = output_dir or Path.home() / ".tunnelshell" / "recordings"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self._events: List[RecordingEvent] = []
        self._start_time: Optional[float] = None
        self._last_event_time: Optional[float] = None
        self._recording_file: Optional[Path] = None
        self._is_recording = False
        
    @property
    def recording_path(self) -> Path:
        """Path to recording file."""
        return self.output_dir / f"{self.session_id}.jsonl"
        
    @property
    def metadata_path(self) -> Path:
        """Path to metadata file."""
        return self.output_dir / f"{self.session_id}.meta.json"
        
    def start(self) -> None:
        """Start recording."""
        if self._is_recording:
            return
            
        self._is_recording = True
        self._start_time = time.time()
        self._last_event_time = self._start_time
        
        # Write initial metadata
        self._write_metadata()
        
    def stop(self) -> None:
        """Stop recording."""
        if not self._is_recording:
            return
            
        self._is_recording = False
        
        # Write final metadata
        self._write_metadata(final=True)
        
    def record_input(self, data: str) -> None:
        """Record input data."""
        self._record_event('input', data)
        
    def record_output(self, data: str) -> None:
        """Record output data."""
        self._record_event('output', data)
        
    def record_resize(self, rows: int, cols: int) -> None:
        """Record terminal resize."""
        self._record_event('resize', f"{rows}x{cols}")
        
    def _record_event(self, event_type: str, data: str) -> None:
        """Record a single event."""
        if not self._is_recording:
            return
            
        now = time.time()
        delay = now - self._last_event_time if self._last_event_time else 0.0
        
        event = RecordingEvent(
            timestamp=now,
            event_type=event_type,
            data=data,
            delay=delay,
        )
        
        self._events.append(event)
        self._last_event_time = now
        
        # Append to file
        self._append_event(event)
        
    def _append_event(self, event: RecordingEvent) -> None:
        """Append event to recording file."""
        with open(self.recording_path, 'a') as f:
            f.write(json.dumps(asdict(event)) + '\n')
            
    def _write_metadata(self, final: bool = False) -> None:
        """Write metadata file."""
        end_time = time.time() if final else None
        duration = (end_time - self._start_time) if self._start_time and end_time else 0.0
        
        file_size = 0
        if self.recording_path.exists():
            file_size = self.recording_path.stat().st_size
            
        metadata = RecordingMetadata(
            session_id=self.session_id,
            session_name=self.session_name,
            host=self.host,
            start_time=self._start_time or time.time(),
            end_time=end_time,
            duration=duration,
            event_count=len(self._events),
            file_size=file_size,
        )
        
        with open(self.metadata_path, 'w') as f:
            json.dump(metadata.to_dict(), f, indent=2)
            
    def get_stats(self) -> dict:
        """Get recording statistics."""
        return {
            "is_recording": self._is_recording,
            "event_count": len(self._events),
            "duration": time.time() - self._start_time if self._start_time else 0,
            "file_size": self.recording_path.stat().st_size if self.recording_path.exists() else 0,
        }


class SessionReplay:
    """Replay recorded sessions."""
    
    def __init__(self, recording_path: Path):
        self.recording_path = recording_path
        self.metadata_path = recording_path.with_suffix('.meta.json')
        self._metadata: Optional[RecordingMetadata] = None
        self._events: List[RecordingEvent] = []
        
    def load(self) -> None:
        """Load recording from file."""
        # Load metadata
        if self.metadata_path.exists():
            with open(self.metadata_path) as f:
                data = json.load(f)
                self._metadata = RecordingMetadata(**data)
                
        # Load events
        self._events = []
        if self.recording_path.exists():
            with open(self.recording_path) as f:
                for line in f:
                    if line.strip():
                        event_data = json.loads(line)
                        self._events.append(RecordingEvent(**event_data))
                        
    @property
    def metadata(self) -> Optional[RecordingMetadata]:
        """Get recording metadata."""
        return self._metadata
        
    @property
    def events(self) -> List[RecordingEvent]:
        """Get recording events."""
        return self._events
        
    def get_output(self) -> str:
        """Get all output as a single string."""
        return ''.join(e.data for e in self._events if e.event_type == 'output')
        
    def get_timeline(self) -> List[dict]:
        """Get event timeline."""
        return [
            {
                "time": e.timestamp,
                "delay": e.delay,
                "type": e.event_type,
                "preview": e.data[:50] + "..." if len(e.data) > 50 else e.data,
            }
            for e in self._events
        ]


def list_recordings(output_dir: Optional[Path] = None) -> List[dict]:
    """List all available recordings."""
    output_dir = output_dir or Path.home() / ".tunnelshell" / "recordings"
    
    recordings = []
    for meta_file in output_dir.glob("*.meta.json"):
        try:
            with open(meta_file) as f:
                data = json.load(f)
                recordings.append(data)
        except Exception:
            continue
            
    return sorted(recordings, key=lambda x: x.get('start_time', 0), reverse=True)


def get_recording(session_id: str, output_dir: Optional[Path] = None) -> Optional[SessionReplay]:
    """Get a recording by session ID."""
    output_dir = output_dir or Path.home() / ".tunnelshell" / "recordings"
    recording_path = output_dir / f"{session_id}.jsonl"
    
    if not recording_path.exists():
        return None
        
    replay = SessionReplay(recording_path)
    replay.load()
    return replay