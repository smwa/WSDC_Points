const getDatabase = async () => {
  const response = await fetch("assets/database.txt");
  return await MessagePack.decodeAsync(response.body);
};

const getEventsDatabase = async () => {
  const response = await fetch("assets/events.txt");
  return await MessagePack.decodeAsync(response.body);
};
