// Carrega as variáveis de ambiente do arquivo .env
require('dotenv').config();

// Importação dos módulos necessários
const express = require('express');
const cors = require('cors');
const mongoose = require('mongoose');
const { getPlaylistDetails } = require('./youtube-api');
const Course = require('./models/Course');

// Configuração do aplicativo Express
const app = express();
const PORT = process.env.PORT || 5000;
const MONGO_URI = 'mongodb://localhost:27017/course-organizer';

// Conexão com o MongoDB
mongoose.connect(MONGO_URI, { useNewUrlParser: true, useUnifiedTopology: true })
  .then(() => console.log('MongoDB conectado com sucesso.'))
  .catch(err => console.error('Erro ao conectar ao MongoDB:', err));

// Middlewares
app.use(cors());
app.use(express.json());

// Rota de teste
app.get('/', (req, res) => {
  res.send('Backend do Organizador de Cursos do YouTube está no ar!');
});

// --- Rotas da API ---

/**
 * Rota para adicionar um novo curso a partir de uma URL de playlist do YouTube.
 * Extrai o ID da playlist, busca os detalhes (simulado), e salva no banco de dados.
 */
app.post('/api/playlists', async (req, res) => {
  const { playlistUrl } = req.body;
  console.log('URL da Playlist Recebida:', playlistUrl);

  try {
    // Extrai o ID da playlist da URL (exemplo simples)
    const playlistId = new URL(playlistUrl).searchParams.get('list');
    if (!playlistId) {
      return res.status(400).json({ message: 'URL da playlist inválida.' });
    }

    const existingCourse = await Course.findOne({ playlistId });
    if (existingCourse) {
      return res.status(409).json({ message: 'Este curso já foi adicionado.' });
    }

    const playlistDetails = await getPlaylistDetails(playlistId, process.env.YOUTUBE_API_KEY);

    const newCourse = new Course({
      playlistId,
      title: playlistDetails.title,
      description: playlistDetails.description,
      videos: playlistDetails.videos.map(v => ({ videoId: v.id, title: v.title, durationInSeconds: v.durationInSeconds }))
    });

    await newCourse.save();
    res.status(201).json(newCourse);

  } catch (error) {
    console.error('Erro ao processar a playlist:', error);
    res.status(500).json({ message: 'Erro ao processar a playlist.' });
  }
});

/**
 * Rota para buscar todos os cursos salvos no banco de dados.
 */
app.get('/api/courses', async (req, res) => {
  try {
    const courses = await Course.find();
    res.status(200).json(courses);
  } catch (error) {
    console.error('Erro ao buscar cursos:', error);
    res.status(500).json({ message: 'Erro ao buscar cursos.' });
  }
});

/**
 * Rota para buscar os detalhes de um curso específico pelo seu ID.
 * Também atualiza o campo `lastAccessed` para a data/hora atual.
 */
app.get('/api/courses/:id', async (req, res) => {
  try {
    const course = await Course.findByIdAndUpdate(
      req.params.id,
      { lastAccessed: Date.now() },
      { new: true }
    );

    if (!course) {
      return res.status(404).json({ message: 'Curso não encontrado.' });
    }
    res.status(200).json(course);
  } catch (error) {
    console.error('Erro ao buscar detalhes do curso:', error);
    res.status(500).json({ message: 'Erro ao buscar detalhes do curso.' });
  }
});

/**
 * Rota para atualizar o status de 'assistido' de um vídeo específico.
 */
app.patch('/api/courses/:courseId/videos/:videoId', async (req, res) => {
  try {
    const { courseId, videoId } = req.params;
    const { watched } = req.body;

    const course = await Course.findOneAndUpdate(
      { _id: courseId, 'videos.videoId': videoId },
      { $set: { 'videos.$.watched': watched } },
      { new: true }
    );

    if (!course) {
      return res.status(404).json({ message: 'Curso ou vídeo não encontrado.' });
    }

    res.status(200).json(course);
  } catch (error) {
    console.error('Erro ao atualizar o status do vídeo:', error);
    res.status(500).json({ message: 'Erro ao atualizar o status do vídeo.' });
  }
});

app.listen(PORT, () => {
  console.log(`Servidor rodando na porta ${PORT}`);
});
