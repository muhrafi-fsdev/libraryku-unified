// Dijalankan MongoDB hanya saat volume data masih kosong (inisialisasi pertama).
// Membuat pengguna khusus aplikasi dengan hak readWrite hanya pada database LibraryKu NoSQL.
// Aman dijalankan ulang: pengguna dan koleksi dibuat hanya bila belum ada.
const dbName = process.env.MONGO_APP_DB;
const appUser = process.env.MONGO_APP_USER;
const appPassword = process.env.MONGO_APP_PASSWORD;

if (!dbName || !appUser || !appPassword) {
  throw new Error('Variabel MONGO_APP_DB, MONGO_APP_USER, dan MONGO_APP_PASSWORD wajib diisi.');
}

const target = db.getSiblingDB(dbName);
if (target.getUser(appUser) === null) {
  target.createUser({ user: appUser, pwd: appPassword, roles: [{ role: 'readWrite', db: dbName }] });
  print('Pengguna aplikasi dibuat.');
} else {
  print('Pengguna aplikasi sudah ada.');
}
if (!target.getCollectionNames().includes('books')) {
  target.createCollection('books');
  print('Koleksi books dibuat.');
}
