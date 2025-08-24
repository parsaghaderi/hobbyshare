// Minimal Canada locations dataset (can be expanded)
// Structure: { provinceCode: { name: 'Ontario', cities: { 'Toronto': ['Downtown','Scarborough','North York','Etobicoke'], ... } } }
window.CANADA_LOCATIONS = {
  ON: { name: 'Ontario', cities: { 'Toronto': ['Downtown','Scarborough','North York','Etobicoke','York'], 'Ottawa': ['Centretown','Kanata','Nepean','Orleans'], 'Hamilton': ['Ancaster','Dundas','Stoney Creek'] } },
  BC: { name: 'British Columbia', cities: { 'Vancouver': ['Downtown','Kitsilano','Gastown','Yaletown'], 'Victoria': ['Downtown','Oak Bay','James Bay'], 'Surrey': ['Guildford','Newton','Whalley'] } },
  QC: { name: 'Quebec', cities: { 'Montreal': ['Ahuntsic',
                                                'Cartierville',
                                                'Bois-de-Saraguay',
                                                'Bordeaux',
                                                'Anjou',
                                                'Côte-des-Neiges',
                                                'Notre-Dame-de-Grâce (NDG)',
                                                'Lachine',
                                                'LaSalle',
                                                'Mile End',
                                                'Le Plateau',
                                                'Milton-Parc',
                                                'Griffintown',
                                                'Little Burgundy (La Petite-Bourgogne)',
                                                'Pointe-Saint-Charles',
                                                'Saint-Henri',
                                                'Ville-Émard',
                                                'Côte-Saint-Paul',
                                                'L’Île-Bizard',
                                                'Sainte-Geneviève',
                                                'Hochelaga-Maisonneuve (HoMa)',
                                                'Mercier-Est',
                                                'Mercier-Ouest',
                                                'Montréal-Nord',
                                                'Outremont',
                                                'Pierrefonds',
                                                'Roxboro',
                                                'Rivière-des-Prairies',
                                                'Pointe-aux-Trembles',
                                                'La Pointe-aux-Prairies',
                                                'Rosemont',
                                                'Petite-Italie (Little Italy)',
                                                'La Petite-Patrie',
                                                'Vieux-Rosemont',
                                                'Saint-Laurent',
                                                'Saint-Léonard',
                                                'Verdun',
                                                'Île-des-Sœurs (Nun’s Island)',
                                                'Downtown (Centre-Ville)',
                                                'Chinatown',
                                                'Gay Village (Le Village)',
                                                'Quartier Latin',
                                                'Old Montreal (Vieux-Montréal)',
                                                'Golden Square Mile',
                                                'Faubourg Saint-Laurent',
                                                'Shaughnessy Village',
                                                'Villeray',
                                                'Saint-Michel',
                                                'Parc-Extension'],
                                                'Quebec City': ['Old Quebec','Montcalm'],
                                                'Laval': ['Chomedey','Sainte-Dorothee'] } },
  AB: { name: 'Alberta', cities: { 'Calgary': ['Downtown','Beltline','Kensington'], 'Edmonton': ['Downtown','Strathcona','Westmount'] } },
  MB: { name: 'Manitoba', cities: { 'Winnipeg': ['Downtown','St. Boniface','Fort Garry'] } },
  SK: { name: 'Saskatchewan', cities: { 'Saskatoon': ['Riversdale','Nutana'], 'Regina': ['Downtown','Cathedral'] } },
  NS: { name: 'Nova Scotia', cities: { 'Halifax': ['Downtown','North End','South End'] } },
  NB: { name: 'New Brunswick', cities: { 'Moncton': ['Downtown'], 'Fredericton': ['Downtown'] } },
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
