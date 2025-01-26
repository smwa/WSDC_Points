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
