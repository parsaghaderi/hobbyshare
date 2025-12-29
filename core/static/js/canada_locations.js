// Minimal Canada locations dataset (can be expanded)
// Structure: { provinceCode: { name: 'Ontario', cities: { 'Toronto': ['Downtown','Scarborough','North York','Etobicoke'], ... } } }
window.CANADA_LOCATIONS = {
  QC: { name: 'Quebec', cities: { 'Montreal': ['Downtown','Plateau','Griffintown','NDG','Ville-Marie'], 'Quebec City': ['Old Quebec','Montcalm','Saint-Roch'], 'Laval': ['Chomedey','Sainte-Dorothee'] } },
  ON: { name: 'Ontario', cities: { 'Toronto': ['Downtown','North York','Scarborough','Etobicoke'], 'Ottawa': ['Centretown','Kanata','Orleans'], 'Hamilton': ['Downtown','Dundas'], 'Mississauga': ['Square One','Port Credit'] } },
  AB: { name: 'Alberta', cities: { 'Calgary': ['Downtown','Beltline','Kensington'], 'Edmonton': ['Downtown','Strathcona','Westmount'], 'Red Deer': ['Downtown'] } },
  BC: { name: 'British Columbia', cities: { 'Vancouver': ['Downtown','Kitsilano','Mount Pleasant'], 'Victoria': ['Downtown','Fernwood'], 'Surrey': ['Guildford','Newton'] } },
  MB: { name: 'Manitoba', cities: { 'Winnipeg': ['Downtown','St. Boniface','Fort Garry'] } },
  SK: { name: 'Saskatchewan', cities: { 'Saskatoon': ['Riversdale','Nutana'], 'Regina': ['Downtown','Cathedral'] } },
  NS: { name: 'Nova Scotia', cities: { 'Halifax': ['Downtown','North End','South End'] } },
  NB: { name: 'New Brunswick', cities: { 'Moncton': ['Downtown'], 'Fredericton': ['Downtown'], 'Saint John': ['Uptown'] } },
  NL: { name: 'Newfoundland and Labrador', cities: { 'St. John\'s': ['Downtown','Quidi Vidi'] } },
  PE: { name: 'Prince Edward Island', cities: { 'Charlottetown': ['Downtown'] } },
  YT: { name: 'Yukon', cities: { 'Whitehorse': ['Downtown'] } },
  NT: { name: 'Northwest Territories', cities: { 'Yellowknife': ['Downtown'] } },
  NU: { name: 'Nunavut', cities: { 'Iqaluit': ['Downtown'] } }
};

function populateLocationSelectors(provinceSel, citySel, neighbourhoodInput, initialProvince, initialCity) {
  if(!window.CANADA_LOCATIONS) return;
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
