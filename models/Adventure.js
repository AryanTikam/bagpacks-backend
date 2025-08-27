// filepath: /home/aryan/Desktop/bagpack/backend/models/Adventure.js
const mongoose = require('mongoose');

const adventureSchema = new mongoose.Schema({
  userId: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'User',
    required: true
  },
  destination: {
    type: String,
    required: true
  },
  places: [{
    name: String,
    coords: [Number, Number]
  }],
  itinerary: {
    text: String,
    generatedAt: {
      type: Date,
      default: Date.now
    }
  },
  options: {
    days: {
      type: Number,
      default: 3
    },
    budget: {
      type: Number,
      default: 10000
    },
    people: {
      type: Number,
      default: 2
    }
  },
  createdAt: {
    type: Date,
    default: Date.now
  }
});

module.exports = mongoose.model('Adventure', adventureSchema);