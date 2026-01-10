import { useState, useEffect } from 'react';

export const useTypewriter = (text, speed = 10, enabled = true) => {
    const [displayedText, setDisplayedText] = useState('');
    const [isComplete, setIsComplete] = useState(false);

    useEffect(() => {
        if (!enabled) {
            setDisplayedText(text);
            setIsComplete(true);
            return;
        }

        let i = 0;
        setDisplayedText('');
        setIsComplete(false);

        const timer = setInterval(() => {
            if (i < text.length) {
                setDisplayedText((prev) => prev + text.charAt(i));
                i++;
            } else {
                clearInterval(timer);
                setIsComplete(true);
            }
        }, speed);

        return () => clearInterval(timer);
    }, [text, speed, enabled]);

    return { displayedText, isComplete };
};
