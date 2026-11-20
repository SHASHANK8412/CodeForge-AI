import React, { useEffect, useRef, useState } from 'react';
import { FaMicrophone, FaStop, FaSpinner } from 'react-icons/fa';
import { transcribeAudio } from '../services/speech';

const MAX_SECONDS = 120;

/**
 * Mic button: records a spoken request in the browser, sends it to the backend, which transcribes it on this machine
 * (faster-whisper), and hands the text to `onTranscript`. Nothing is sent to a third-party speech service.
 */
export default function VoiceInputButton({ onTranscript, className = '' }) {
  const [state, setState] = useState('idle'); // idle | recording | transcribing
  const [seconds, setSeconds] = useState(0);
  const [error, setError] = useState('');
  const recorder = useRef(null);
  const chunks = useRef([]);
  const timer = useRef(null);

  const supported = typeof window !== 'undefined' && !!navigator.mediaDevices?.getUserMedia && typeof MediaRecorder !== 'undefined';

  useEffect(() => () => {
    clearInterval(timer.current);
    recorder.current?.stream?.getTracks().forEach((t) => t.stop());
  }, []);

  const stop = () => {
    clearInterval(timer.current);
    if (recorder.current && recorder.current.state === 'recording') recorder.current.stop();
  };

  const start = async () => {
    setError('');
    let stream;
    try {
      stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    } catch {
      setError('Microphone access was blocked. Allow it in the browser to use voice input.');
      return;
    }
    const mime = ['audio/webm;codecs=opus', 'audio/webm', 'audio/ogg', 'audio/mp4'].find((m) => MediaRecorder.isTypeSupported?.(m)) || '';
    const rec = new MediaRecorder(stream, mime ? { mimeType: mime } : undefined);
    chunks.current = [];
    rec.ondataavailable = (e) => { if (e.data.size) chunks.current.push(e.data); };
    rec.onstop = async () => {
      stream.getTracks().forEach((t) => t.stop());
      const blob = new Blob(chunks.current, { type: rec.mimeType || 'audio/webm' });
      if (!blob.size) { setState('idle'); return; }
      setState('transcribing');
      try {
        const { text } = await transcribeAudio(blob);
        if (text) onTranscript(text);
        else setError('No speech was recognised. Try again a little closer to the microphone.');
      } catch (err) {
        setError(err.message);
      } finally {
        setState('idle');
      }
    };
    recorder.current = rec;
    rec.start();
    setSeconds(0);
    setState('recording');
    timer.current = setInterval(() => {
      setSeconds((s) => {
        if (s + 1 >= MAX_SECONDS) stop();
        return s + 1;
      });
    }, 1000);
  };

  if (!supported) return null;

  const label = state === 'recording' ? `Stop recording (${seconds}s)` : state === 'transcribing' ? 'Transcribing…' : 'Speak your request';
  return (
    <div className={`flex flex-col items-start gap-1 ${className}`}>
      <button
        type="button"
        onClick={state === 'recording' ? stop : start}
        disabled={state === 'transcribing'}
        aria-label={label}
        title={label}
        className={`inline-flex items-center gap-2 rounded-full border px-3 py-1 text-xs transition cursor-pointer disabled:cursor-wait ${
          state === 'recording'
            ? 'border-red-500/60 bg-red-500/10 text-red-300 hover:bg-red-500/20'
            : 'border-border-dark bg-surface-elevated text-text-secondary hover:border-accent-violet/50 hover:text-text-primary'
        }`}
      >
        {state === 'recording' ? <FaStop /> : state === 'transcribing' ? <FaSpinner className="animate-spin" /> : <FaMicrophone />}
        <span>{state === 'recording' ? `Stop · ${seconds}s` : state === 'transcribing' ? 'Transcribing…' : 'Speak'}</span>
      </button>
      {error && <span role="alert" className="text-xs text-red-300">{error}</span>}
    </div>
  );
}
