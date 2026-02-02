import { useState, useRef, useCallback } from 'react';
import apiClient from 'api/apiClient';

/**
 * Hook for recording audio and transcribing via local Whisper.
 * Uses MediaRecorder API with webm/opus format.
 */
export const useVoiceRecorder = (onTranscription) => {
    const [isRecording, setIsRecording] = useState(false);
    const [isTranscribing, setIsTranscribing] = useState(false);
    const [error, setError] = useState(null);

    const mediaRecorderRef = useRef(null);
    const audioChunksRef = useRef([]);

    const startRecording = useCallback(async () => {
        setError(null);
        audioChunksRef.current = [];

        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            const mediaRecorder = new MediaRecorder(stream, {
                mimeType: 'audio/webm;codecs=opus'
            });

            mediaRecorderRef.current = mediaRecorder;

            mediaRecorder.ondataavailable = (event) => {
                if (event.data.size > 0) {
                    audioChunksRef.current.push(event.data);
                }
            };

            mediaRecorder.onstop = async () => {
                // Stop all tracks
                stream.getTracks().forEach(track => track.stop());

                const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
                await transcribeAudio(audioBlob);
            };

            mediaRecorder.start(250); // Collect data every 250ms for reliable chunking
            setIsRecording(true);

        } catch (err) {
            console.error('Failed to start recording:', err);
            setError('Microphone access denied or unavailable.');
        }
    }, []);

    const stopRecording = useCallback(() => {
        if (mediaRecorderRef.current && isRecording) {
            mediaRecorderRef.current.stop();
            setIsRecording(false);
        }
    }, [isRecording]);

    const transcribeAudio = async (audioBlob) => {
        setIsTranscribing(true);
        setError(null);

        try {
            const formData = new FormData();
            formData.append('file', audioBlob, 'recording.webm');

            const response = await apiClient.post('/api/transcribe', formData, {
                headers: { 'Content-Type': 'multipart/form-data' }
            });

            if (response.data?.text && onTranscription) {
                onTranscription(response.data.text);
            }
        } catch (err) {
            console.error('Transcription failed:', err);
            setError('Transcription failed. Please try again.');
        } finally {
            setIsTranscribing(false);
        }
    };

    return {
        isRecording,
        isTranscribing,
        error,
        startRecording,
        stopRecording
    };
};

export default useVoiceRecorder;
