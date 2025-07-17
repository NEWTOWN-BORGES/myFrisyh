import React from 'react';
import { Link } from 'react-router-dom';
import { formatDuration } from '../utils/formatters';

const CourseList = ({ courses }) => {
  const calculateProgress = (videos) => {
    if (!videos || videos.length === 0) return { watched: 0, total: 0, watchedTime: 0, totalTime: 0 };
    const watchedCount = videos.filter(v => v.watched).length;
    const totalTime = videos.reduce((sum, v) => sum + v.durationInSeconds, 0);
    const watchedTime = videos.filter(v => v.watched).reduce((sum, v) => sum + v.durationInSeconds, 0);
    return { watched: watchedCount, total: videos.length, watchedTime, totalTime };
  };

  return (
    <div>
      <h2>Meus Cursos</h2>
      {courses.length === 0 ? (
        <p>Nenhum curso adicionado ainda.</p>
      ) : (
        <ul>
          {courses.map((course) => {
            const progress = calculateProgress(course.videos);
            return (
              <li key={course._id} style={{ listStyle: 'none', margin: '10px 0', border: '1px solid #ccc', padding: '10px' }}>
                <Link to={`/course/${course._id}`} style={{ textDecoration: 'none', color: 'inherit' }}>
                  <h3>{course.title}</h3>
                  <p>Progresso: {progress.watched}/{progress.total} aulas</p>
                  <p>Tempo: {formatDuration(progress.watchedTime)} / {formatDuration(progress.totalTime)}</p>
                  <p style={{ fontSize: '0.8em', color: '#666' }}>
                    Último acesso: {new Date(course.lastAccessed).toLocaleDateString('pt-BR')}
                  </p>
                </Link>
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
};

export default CourseList;
