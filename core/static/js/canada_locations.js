// Minimal Canada locations dataset (can be expanded)
// Structure: { provinceCode: { name: 'Ontario', cities: { 'Toronto': ['Downtown','Scarborough','North York','Etobicoke'], ... } } }
// Fallback data in case the API fetch fails (ensures Ontario/major cities still render)
const FALLBACK_CANADA_LOCATIONS = {
  "QC": { "name": "Quebec", "cities": { "Montreal": [], "Quebec City": [], "Laval": [], "Gatineau": [], "Longueuil": [], "Sherbrooke": [], "Saguenay": [], "Trois-Rivieres": [], "Terrebonne": [], "Levis": [] } },
  "ON": { "name": "Ontario", "cities": { "Toronto": [], "Ottawa": [], "Mississauga": [], "Brampton": [], "Hamilton": [], "London": [], "Markham": [], "Vaughan": [], "Kitchener": [], "Waterloo": [], "Windsor": [], "Richmond Hill": [], "Oakville": [], "Burlington": [], "Oshawa": [], "St. Catharines": [], "Barrie": [], "Guelph": [], "Kingston": [], "Sudbury": [] } },
  "AB": { "name": "Alberta", "cities": { "Calgary": [], "Edmonton": [], "Red Deer": [], "Lethbridge": [], "St. Albert": [], "Medicine Hat": [], "Grande Prairie": [], "Fort McMurray": [] } },
  "BC": { "name": "British Columbia", "cities": { "Vancouver": [], "Surrey": [], "Burnaby": [], "Richmond": [], "Abbotsford": [], "Coquitlam": [], "Kelowna": [], "Victoria": [], "Nanaimo": [], "Kamloops": [], "Langley": [], "Delta": [] } },
  "MB": { "name": "Manitoba", "cities": { "Winnipeg": [], "Brandon": [], "Steinbach": [], "Thompson": [], "Portage la Prairie": [] } },
  "SK": { "name": "Saskatchewan", "cities": { "Saskatoon": [], "Regina": [], "Prince Albert": [], "Moose Jaw": [], "Swift Current": [] } },
  "NS": { "name": "Nova Scotia", "cities": { "Halifax": [], "Sydney": [], "Dartmouth": [], "Truro": [] } },
  "NB": { "name": "New Brunswick", "cities": { "Moncton": [], "Fredericton": [], "Saint John": [], "Dieppe": [], "Miramichi": [] } },
  "NL": { "name": "Newfoundland and Labrador", "cities": { "St. John's": [], "Mount Pearl": [], "Corner Brook": [], "Gander": [] } },
  "PE": { "name": "Prince Edward Island", "cities": { "Charlottetown": [], "Summerside": [] } },
  "YT": { "name": "Yukon", "cities": { "Whitehorse": [] } },
  "NT": { "name": "Northwest Territories", "cities": { "Yellowknife": [] } },
  "NU": { "name": "Nunavut", "cities": { "Iqaluit": [] } }
};

window.CANADA_LOCATIONS = window.CANADA_LOCATIONS || {};

let _locationsPromise = null;
function ensureCanadaLocations() {
  if (_locationsPromise) return _locationsPromise;
  _locationsPromise = fetch('/api/locations/canada/?v=3')
    .then(res => res.json())
    .then(data => {
      window.CANADA_LOCATIONS = data && Object.keys(data).length ? data : FALLBACK_CANADA_LOCATIONS;
      return window.CANADA_LOCATIONS;
    })
    .catch(err => {
      console.warn('Failed to load Canada locations from API, using fallback.', err);
      window.CANADA_LOCATIONS = FALLBACK_CANADA_LOCATIONS;
      return window.CANADA_LOCATIONS;
    });
  return _locationsPromise;
}

function populateLocationSelectors(provinceSel, citySel, neighbourhoodInput, initialProvince, initialCity, initialNeighbourhood) {
  function renderSelectors() {
    if(!window.CANADA_LOCATIONS || Object.keys(window.CANADA_LOCATIONS).length === 0) return;
    provinceSel.innerHTML = '<option value="">Province</option>';
    Object.entries(CANADA_LOCATIONS).forEach(([code, data]) => {
      const opt = document.createElement('option');
      opt.value = data.name;
      opt.textContent = data.name;
      if(initialProvince && initialProvince.toLowerCase() === data.name.toLowerCase()) opt.selected = true;
      provinceSel.appendChild(opt);
    });

    let neighbourhoodDatalist = null;
    function ensureNeighbourhoodDatalist() {
      if (!neighbourhoodInput) return null;
      if (!neighbourhoodDatalist) {
        neighbourhoodDatalist = document.createElement('datalist');
        neighbourhoodDatalist.id = `${neighbourhoodInput.id}-suggestions`;
        neighbourhoodInput.setAttribute('list', neighbourhoodDatalist.id);
        neighbourhoodInput.insertAdjacentElement('afterend', neighbourhoodDatalist);
      }
      return neighbourhoodDatalist;
    }

    function refreshNeighbourhoods() {
      if (!neighbourhoodInput) return;
      const selectedProvName = provinceSel.value;
      const selectedCityName = citySel.value;
      const dl = ensureNeighbourhoodDatalist();
      if (!dl) return;
      dl.innerHTML = '';
      neighbourhoodInput.placeholder = selectedCityName ? 'Neighbourhood (optional)' : 'Neighbourhood';
      if (!selectedProvName || !selectedCityName) return;
      const provEntry = Object.values(CANADA_LOCATIONS).find(p => p.name === selectedProvName);
      if (!provEntry) return;
      const neighbourhoods = provEntry.cities[selectedCityName] || [];
      neighbourhoods.forEach(name => {
        const opt = document.createElement('option');
        opt.value = name;
        dl.appendChild(opt);
      });
      if (initialNeighbourhood) {
        neighbourhoodInput.value = initialNeighbourhood;
        initialNeighbourhood = null;
      }
    }

    function refreshCities() {
      const selectedProvName = provinceSel.value;
      citySel.innerHTML = '<option value="">City</option>';
      neighbourhoodInput && (neighbourhoodInput.placeholder = 'Neighbourhood');
      if (neighbourhoodInput && !initialNeighbourhood) neighbourhoodInput.value = '';
      if(!selectedProvName) return;
      const provEntry = Object.values(CANADA_LOCATIONS).find(p => p.name === selectedProvName);
      if(!provEntry) return;
      Object.keys(provEntry.cities).forEach(cityName => {
        const opt = document.createElement('option');
        opt.value = cityName;
        opt.textContent = cityName;
        if(initialCity && initialCity.toLowerCase() === cityName.toLowerCase()) opt.selected = true;
        citySel.appendChild(opt);
      });
    }

    provinceSel.addEventListener('change', () => {
      initialCity = null;
      initialNeighbourhood = null;
      refreshCities();
      refreshNeighbourhoods();
    });
    citySel.addEventListener('change', () => {
      initialNeighbourhood = null;
      refreshNeighbourhoods();
    });
    refreshCities();
    refreshNeighbourhoods();
  }

  // Load from API, then render.
  ensureCanadaLocations().then(renderSelectors);
}
