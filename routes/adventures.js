const express = require('express');
const Adventure = require('../models/Adventure');
const auth = require('../middleware/auth');

const router = express.Router();

// Save adventure
router.post('/', auth, async (req, res) => {
  try {
    const { destination, places, itinerary, options } = req.body;
    
    // Only save if there's an itinerary
    if (!itinerary || !itinerary.text) {
      return res.status(400).json({ message: 'Itinerary is required' });
    }
    
    const adventure = new Adventure({
      userId: req.user._id,
      destination,
      places,
      itinerary,
      options
    });

    await adventure.save();
    res.status(201).json(adventure);
  } catch (error) {
    res.status(500).json({ message: error.message });
  }
});

// Get user's adventures (only those with itineraries)
router.get('/', auth, async (req, res) => {
  try {
    const adventures = await Adventure.find({ 
      userId: req.user._id,
      'itinerary.text': { $exists: true, $ne: '' }
    }).sort({ createdAt: -1 });
    res.json(adventures);
  } catch (error) {
    res.status(500).json({ message: error.message });
  }
});

// Get specific adventure by ID
router.get('/:id', auth, async (req, res) => {
  try {
    const adventure = await Adventure.findOne({
      _id: req.params.id,
      userId: req.user._id
    });

    if (!adventure) {
      return res.status(404).json({ message: 'Adventure not found' });
    }

    res.json(adventure);
  } catch (error) {
    res.status(500).json({ message: error.message });
  }
});

// Delete adventure
router.delete('/:id', auth, async (req, res) => {
  try {
    const adventure = await Adventure.findOneAndDelete({
      _id: req.params.id,
      userId: req.user._id
    });

    if (!adventure) {
      return res.status(404).json({ message: 'Adventure not found' });
    }

    res.json({ message: 'Adventure deleted successfully' });
  } catch (error) {
    res.status(500).json({ message: error.message });
  }
});

module.exports = router;