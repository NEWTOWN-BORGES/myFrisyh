import React, { useState } from 'react';
import api from '../api';

const CourseForm = ({ onCourseAdded }) => {
  const [playlistUrl, setPlaylistUrl] = useState('');
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    try {
      const response = await api.post('/playlists', { playlistUrl });
      console.log('Curso adicionado:', response.data);
      onCourseAdded(response.data); // Callback para atualizar a lista de cursos
      setPlaylistUrl('');
    } catch (err) {
      setError(err.response?.data?.message || 'Ocorreu um erro.');
      console.error(err);
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <input
        type="text"
        placeholder="Cole o link da playlist do YouTube aqui"
        value={playlistUrl}
        onChange={(e) => setPlaylistUrl(e.target.value)}
        style={{ width: '400px', padding: '10px' }}
      />
      <button type="submit" style={{ padding: '10px' }}>
        Adicionar Curso
      </button>
      {error && <p style={{ color: 'red' }}>{error}</p>}
    </form>
  );
};

export default CourseForm;
