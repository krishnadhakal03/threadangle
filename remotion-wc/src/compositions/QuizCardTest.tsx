import React from 'react';
import { QuizCard } from '../components/QuizCard';

export const QuizCardTest: React.FC = () => (
  <QuizCard
    questionNumber={1}
    totalQuestions={10}
    question="Which country has won the most World Cups?"
    options={{ A: 'Brazil', B: 'Germany', C: 'Italy' }}
    correctAnswer="A"
    explanation="Brazil — 5 titles (1958, 62, 70, 94, 2002)"
    imageUrl="https://images.pexels.com/photos/46798/the-ball-stadion-football-the-pitch-46798.jpeg"
    themeColor="#2196F3"
    revealFrame={300}
    totalFrames={900}
  />
);
