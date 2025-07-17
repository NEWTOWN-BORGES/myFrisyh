const mongoose = require('mongoose');

const videoSchema = new mongoose.Schema({
  videoId: { type: String, required: true },
  title: { type: String, required: true },
  durationInSeconds: { type: Number, required: true },
  watched: { type: Boolean, default: false },
});

const courseSchema = new mongoose.Schema({
  playlistId: { type: String, required: true, unique: true },
  title: { type: String, required: true },
  description: { type: String },
  videos: [videoSchema],
  lastAccessed: { type: Date, default: Date.now },
});

const Course = mongoose.model('Course', courseSchema);

module.exports = Course;
