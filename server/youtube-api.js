const { google } = require('googleapis');

// Função para converter a duração do formato ISO 8601 para segundos
const parseISO8601Duration = (duration) => {
  const match = duration.match(/PT(\d+H)?(\d+M)?(\d+S)?/);

  const hours = (parseInt(match[1]) || 0);
  const minutes = (parseInt(match[2]) || 0);
  const seconds = (parseInt(match[3]) || 0);

  return hours * 3600 + minutes * 60 + seconds;
};

const getPlaylistDetails = async (playlistId, apiKey) => {
  const youtube = google.youtube({
    version: 'v3',
    auth: apiKey,
  });

  // 1. Obter detalhes da playlist (título, descrição)
  const playlistResponse = await youtube.playlists.list({
    part: 'snippet',
    id: playlistId,
  });

  const playlist = playlistResponse.data.items[0];
  if (!playlist) {
    throw new Error('Playlist não encontrada.');
  }

  // 2. Obter os vídeos da playlist
  let videoItems = [];
  let nextPageToken = null;
  do {
    const playlistItemsResponse = await youtube.playlistItems.list({
      part: 'snippet,contentDetails',
      playlistId: playlistId,
      maxResults: 50, // Máximo permitido pela API
      pageToken: nextPageToken,
    });

    videoItems = videoItems.concat(playlistItemsResponse.data.items);
    nextPageToken = playlistItemsResponse.data.nextPageToken;
  } while (nextPageToken);

  // 3. Obter a duração de cada vídeo
  const videoIds = videoItems.map(item => item.contentDetails.videoId);
  const videosResponse = await youtube.videos.list({
    part: 'contentDetails',
    id: videoIds.join(','),
  });

  const videoDurations = {};
  videosResponse.data.items.forEach(video => {
    videoDurations[video.id] = parseISO8601Duration(video.contentDetails.duration);
  });

  // 4. Formatar os dados para o nosso modelo
  const videos = videoItems.map(item => ({
    id: item.contentDetails.videoId,
    title: item.snippet.title,
    durationInSeconds: videoDurations[item.contentDetails.videoId] || 0,
  }));

  return {
    title: playlist.snippet.title,
    description: playlist.snippet.description,
    videos: videos,
  };
};

module.exports = { getPlaylistDetails };
