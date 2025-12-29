// Minimal Canada locations dataset (can be expanded)
// Structure: { provinceCode: { name: 'Ontario', cities: { 'Toronto': ['Downtown','Scarborough','North York','Etobicoke'], ... } } }
window.CANADA_LOCATIONS = window.CANADA_LOCATIONS || {};

let _locationsPromise = null;
function ensureCanadaLocations() {
  if (_locationsPromise) return _locationsPromise;
  _locationsPromise = fetch('/api/locations/canada/')
    .then(res => res.json())
    .then(data => {
      window.CANADA_LOCATIONS = data || {};
      return window.CANADA_LOCATIONS;
    })
    .catch(err => {
      console.warn('Failed to load Canada locations from API, using existing data if any.', err);
      return window.CANADA_LOCATIONS || {};
    });
  return _locationsPromise;
}

function populateLocationSelectors(provinceSel, citySel, neighbourhoodInput, initialProvince, initialCity) {
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

    function refreshCities() {
      const selectedProvName = provinceSel.value;
      citySel.innerHTML = '<option value="">City</option>';
      neighbourhoodInput && (neighbourhoodInput.placeholder = 'Neighbourhood');
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

    provinceSel.addEventListener('change', () => { initialCity = null; refreshCities(); });
    refreshCities();
  }

  // Load from API, then render.
  ensureCanadaLocations().then(renderSelectors);
}
