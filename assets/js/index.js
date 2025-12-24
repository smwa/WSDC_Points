const DANCER_CHUNK_SIZE = 20;

const getDatabase = async () => {
  const response = await fetch("assets/database.txt");
  return await MessagePack.decodeAsync(response.body);
};

const getEventsDatabase = async () => {
  const response = await fetch("assets/events.txt");
  return await MessagePack.decodeAsync(response.body);
};

const getDancer = async (id) => {
  const bottom = Math.floor(id / DANCER_CHUNK_SIZE) * DANCER_CHUNK_SIZE;
  const top = bottom + DANCER_CHUNK_SIZE;
  const file = `dancers_${bottom}-${top}.txt`;
  const response = await fetch("assets/chunks/"+file);
  const dancers = (await MessagePack.decodeAsync(response.body)).dancers;
  return dancers.find(dancer => dancer.id === id);
};

const __getLocalStore = () => {
  return JSON.parse(localStorage.wsdcpoints || '{}');
};

const __setLocalStore = (store) => {
  localStorage.wsdcpoints = JSON.stringify(store);
};

const getFavoriteDancers = () => {
  const store = __getLocalStore();
  if (!('favoriteDancers' in store)) {
    return [];
  }
  return store.favoriteDancers;
};

const setFavoriteDancers = (favoriteDancers) => {
  const store = __getLocalStore();
  store.favoriteDancers = favoriteDancers;
  __setLocalStore(store);
};

const getIsFavoritedDancer = (id) => {
  return getFavoriteDancers().includes(id);
};

const addFavoriteDancer = (id) => {
  const fd = getFavoriteDancers();
  fd.push(id);
  setFavoriteDancers(fd);
};

const removeFavoriteDancer = (id) => {
  let fd = getFavoriteDancers();
  fd = fd.filter(_id => _id !== id);
  setFavoriteDancers(fd);
};

const updateIcons = async () => {
  feather.replace();
}

const format_placement_result = (placement) => {
  if (placement === '11') return '11th';
  if (placement === '12') return '12th';
  if (placement === '13') return '13th';
  if (placement.substring(-1) === '1') return `${placement}st`;
  if (placement.substring(-1) === '2') return `${placement}nd`;
  if (placement.substring(-1) === '3') return `${placement}rd`;
  if (parseInt(placement, 10) > 1) return `${placement}th`;
  return placement;
};
