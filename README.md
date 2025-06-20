# Enhanced Astrological Web Application

This is an enhanced version of the astrological web application that calculates astrological charts based on birth information using Swiss Ephemeris.

## New Features

- **Improved Location Handling**:
  - Separate fields for city, state, and country for more accurate geocoding
  - Location search with autocomplete suggestions
  - Support for disambiguating cities with the same name

- **Enhanced Swiss Ephemeris Integration**:
  - Automatic downloading of missing ephemeris files
  - Calculation caching for better performance
  - Support for extended planet sets including asteroids
  - Improved error handling for more reliable calculations

- **Multiple Astrocartography Layers**:
  - **Natal Layer**: Traditional birth chart astrocartography with all planetary lines
  - **Transit Layer**: Current planetary transits overlaid on the map
  - **CCG (Conceptional Continual Gestation) Layer**: Alternative calculation method
  - **Human Design Layer**: Design chart calculated using the 88° solar-arc method

- **Human Design Integration**:
  - Automatic calculation of Design datetime (88° solar-arc before birth)
  - Full feature generation including planet lines, aspects, parans, and hermetic lots
  - Separate toggle controls for Human Design features
  - Redis caching support for improved performance

- **Additional Enhancements**:
  - Timezone auto-detection based on selected location
  - Chart saving/loading functionality
  - Progress indicators for long calculations
  - Responsive design for mobile devices

## Installation

1. Install Python dependencies:
```
pip install -r requirements.txt
```

2. Install Node.js dependencies:
```
cd frontend-src
npm install
```

## Running the Application

1. Start the backend API server:
```
cd backend
python api.py
```

2. Start the frontend development server:
```
cd frontend-src
npm run dev
```

3. Access the application at http://localhost:3000

## Usage

1. Enter your birth date, time, and location details
2. Use the location search feature to find your birth city
3. Select your preferred house system (defaults to Whole Sign)
4. Optionally enable extended planets for more detailed calculations
5. Click "Generate Chart" to view your astrological chart
6. Save your chart for future reference using the chart management tools

## API Endpoints

- `/api/calculate` - Calculate astrological chart
- `/api/astrocartography` - Generate astrocartography features (supports layer_type: 'natal', 'transit', 'CCG', 'HD_DESIGN')
- `/api/house-systems` - Get available house systems
- `/api/timezones` - Get available timezones
- `/api/location-suggestions` - Get location suggestions based on query
- `/api/detect-timezone` - Detect timezone from coordinates

## Testing

Run the test suite to verify functionality:
```
python tests/test_application.py
```

Note: The first run may take some time as it downloads required ephemeris files.
