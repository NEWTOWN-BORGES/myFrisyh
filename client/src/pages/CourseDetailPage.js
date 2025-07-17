import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import ReactPlayer from 'react-player/youtube';
import api from '../api';
import { formatDuration } from '../utils/formatters';

/**
 * Componente para a página de detalhes de um curso.
 * Exibe o player de vídeo e a lista de aulas, permitindo marcar como assistidas.
 */
const CourseDetailPage = () => {
  const { courseId } = useParams();
  const [course, setCourse] = useState(null);
  const [loading, setLoading] = useState(true);
  const [currentVideo, setCurrentVideo] = useState(null);

  // Busca os detalhes do curso da API ao carregar a página
  useEffect(() => {
    const fetchCourse = async () => {
      try {
        setLoading(true);
        const response = await api.get(`/courses/${courseId}`);
        setCourse(response.data);
        // Define o primeiro vídeo como o vídeo atual ao carregar
        if (response.data && response.data.videos.length > 0) {
          setCurrentVideo(response.data.videos[0]);
        }
      } catch (error) {
        console.error('Erro ao buscar detalhes do curso:', error);
      } finally {
        setLoading(false);
      }
    };
    fetchCourse();
  }, [courseId]);

  const handleToggleWatched = async (videoId, watched) => {
    try {
      const updatedCourse = await api.patch(`/courses/${courseId}/videos/${videoId}`, { watched: !watched });
      setCourse(updatedCourse.data);
    } catch (error) {
      console.error('Erro ao atualizar status do vídeo:', error);
    }
  };

  if (loading) {
    return <p>Carregando...</p>;
  }

  if (!course) {
    return <p>Curso não encontrado.</p>;
  }

  return (
    <div>
      <Link to="/">&larr; Voltar para Meus Cursos</Link>
      <h2>{course.title}</h2>

      <div style={{ display: 'flex' }}>
        <div style={{ flex: 1, marginRight: '20px' }}>
          {currentVideo && (
            <ReactPlayer
              url={`https://www.youtube.com/watch?v=${currentVideo.videoId}`}
              controls
              width="100%"
            />
          )}
          <h3>{currentVideo?.title}</h3>
        </div>

        <div style={{ width: '300px' }}>
          <h4>Aulas do Curso</h4>
          <ul style={{ listStyle: 'none', padding: 0 }}>
            {course.videos.map((video) => (
              <li key={video.videoId} style={{ display: 'flex', alignItems: 'center', margin: '10px 0', cursor: 'pointer' }} onClick={() => setCurrentVideo(video)}>
                <input
                  type="checkbox"
                  checked={video.watched}
                  onChange={(e) => {
                    e.stopPropagation(); // Evita que o clique no checkbox troque o vídeo
                    handleToggleWatched(video.videoId, video.watched)}
                  }
                  style={{ marginRight: '10px' }}
                />
                <span>{video.title} ({formatDuration(video.durationInSeconds)})</span>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
};

export default CourseDetailPage;
