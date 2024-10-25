const getDatabase = async () => {
  const response = await fetch("assets/database.txt");
  return await MessagePack.decodeAsync(response.body);
};
