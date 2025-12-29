// Minimal Canada locations dataset (can be expanded)
// Structure: { provinceCode: { name: 'Ontario', cities: { 'Toronto': ['Downtown','Scarborough','North York','Etobicoke'], ... } } }
window.CANADA_LOCATIONS = {
  QC: { name: 'Quebec', cities: {
    'Montreal': ['Downtown','Plateau','Griffintown','NDG','Ville-Marie'],
    'Quebec City': ['Old Quebec','Montcalm','Saint-Roch','Sainte-Foy'],
    'Laval': ['Chomedey','Sainte-Dorothee','Laval-des-Rapides'],
    'Gatineau': ['Hull','Aylmer'],
    'Longueuil': ['Vieux-Longueuil','Greenfield Park'],
    'Sherbrooke': ['Lennoxville'],
    'Saguenay': ['Chicoutimi','Jonquiere'],
    'Trois-Rivieres': ['Cap-de-la-Madeleine'],
    'Terrebonne': ['Lachenaie'],
    'Levis': ['Desjardins']
  } },
  ON: { name: 'Ontario', cities: {
    'Toronto': ['Downtown','North York','Scarborough','Etobicoke'],
    'Ottawa': ['Centretown','Kanata','Orleans'],
    'Mississauga': ['Square One','Port Credit','Streetsville'],
    'Brampton': ['Downtown','Bramalea'],
    'Hamilton': ['Downtown','Dundas','Stoney Creek'],
    'London': ['Downtown','Masonville'],
    'Markham': ['Unionville'],
    'Vaughan': ['Maple','Concord'],
    'Kitchener': ['Downtown'],
    'Waterloo': ['Uptown'],
    'Windsor': ['Downtown'],
    'Richmond Hill': ['Hillcrest'],
    'Oakville': ['Kerr Village'],
    'Burlington': ['Downtown'],
    'Oshawa': ['Downtown'],
    'St. Catharines': ['Downtown'],
    'Barrie': ['Downtown'],
    'Guelph': ['Downtown'],
    'Kingston': ['Downtown'],
    'Sudbury': ['Downtown']
  } },
  AB: { name: 'Alberta', cities: {
    'Calgary': ['Downtown','Beltline','Kensington'],
    'Edmonton': ['Downtown','Strathcona','Westmount'],
    'Red Deer': ['Downtown'],
    'Lethbridge': ['Downtown'],
    'St. Albert': ['Downtown'],
    'Medicine Hat': ['Southlands'],
    'Grande Prairie': ['Avondale'],
    'Fort McMurray': ['Downtown']
  } },
  BC: { name: 'British Columbia', cities: {
    'Vancouver': ['Downtown','Kitsilano','Mount Pleasant'],
    'Surrey': ['Guildford','Newton','Whalley'],
    'Burnaby': ['Metrotown','Brentwood'],
    'Richmond': ['City Centre','Steveston'],
    'Abbotsford': ['Clearbrook'],
    'Coquitlam': ['Town Centre'],
    'Kelowna': ['Downtown'],
    'Victoria': ['Downtown','Fernwood','James Bay'],
    'Nanaimo': ['Downtown'],
    'Kamloops': ['Sahali','North Shore'],
    'Langley': ['City Centre'],
    'Delta': ['Ladner','Tsawwassen']
  } },
  MB: { name: 'Manitoba', cities: {
    'Winnipeg': ['Downtown','St. Boniface','Fort Garry'],
    'Brandon': ['Downtown'],
    'Steinbach': ['Downtown'],
    'Thompson': ['Downtown'],
    'Portage la Prairie': ['Downtown']
  } },
  SK: { name: 'Saskatchewan', cities: {
    'Saskatoon': ['Riversdale','Nutana','Stonebridge'],
    'Regina': ['Downtown','Cathedral','Harbour Landing'],
    'Prince Albert': ['Downtown'],
    'Moose Jaw': ['Downtown'],
    'Swift Current': ['Downtown']
  } },
  NS: { name: 'Nova Scotia', cities: {
    'Halifax': ['Downtown','North End','South End'],
    'Sydney': ['Downtown'],
    'Dartmouth': ['Downtown'],
    'Truro': ['Downtown']
  } },
  NB: { name: 'New Brunswick', cities: {
    'Moncton': ['Downtown'],
    'Fredericton': ['Downtown'],
    'Saint John': ['Uptown'],
    'Dieppe': ['Downtown'],
    'Miramichi': ['Newcastle']
  } },
  NL: { name: 'Newfoundland and Labrador', cities: {
    'St. John\'s': ['Downtown','Quidi Vidi'],
    'Mount Pearl': ['Downtown'],
    'Corner Brook': ['Downtown'],
    'Gander': ['Downtown']
  } },
  PE: { name: 'Prince Edward Island', cities: {
    'Charlottetown': ['Downtown'],
    'Summerside': ['Downtown']
  } },
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
