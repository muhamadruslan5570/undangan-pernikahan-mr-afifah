import { getStore } from "@netlify/blobs";

const store = getStore("guestbook");

export default async (req) => {
  try {
    if (req.method === "GET") {
      const messages = (await store.get("messages", { type: "json" })) || [];
      return Response.json({ messages });
    }

    if (req.method === "POST") {
      const body = await req.json();

      const name = String(body.name || "").trim();
      const status = String(body.status || "").trim();
      const message = String(body.message || "").trim();

      if (!name || !status || !message) {
        return Response.json(
          { detail: "Nama, status, dan ucapan wajib diisi." },
          { status: 400 }
        );
      }

      const messages = (await store.get("messages", { type: "json" })) || [];

      messages.unshift({
        id: Date.now(),
        name,
        status,
        message,
        created_at: new Date().toISOString()
      });

      await store.setJSON("messages", messages);

      return Response.json({
        message: "Ucapan berhasil disimpan.",
        data: messages[0]
      });
    }

    if (req.method === "DELETE") {
      const authHeader = req.headers.get("authorization") || "";
      const expectedToken = process.env.GUESTBOOK_ADMIN_TOKEN || "";

      if (
        !expectedToken ||
        authHeader !== `Bearer ${expectedToken}`
      ) {
        return Response.json(
          { detail: "Unauthorized." },
          { status: 401 }
        );
      }

      const url = new URL(req.url);
      const id = Number(url.searchParams.get("id"));

      if (!Number.isFinite(id)) {
        return Response.json(
          { detail: "ID komentar tidak valid." },
          { status: 400 }
        );
      }

      const messages = (await store.get("messages", { type: "json" })) || [];
      const filtered = messages.filter((item) => item.id !== id);

      if (filtered.length === messages.length) {
        return Response.json(
          { detail: "Komentar tidak ditemukan." },
          { status: 404 }
        );
      }

      await store.setJSON("messages", filtered);

      return Response.json({
        message: "Ucapan berhasil dihapus."
      });
    }

    return new Response("Method Not Allowed", { status: 405 });
  } catch (error) {
    console.error(error);
    return Response.json(
      { detail: "Terjadi kesalahan pada server." },
      { status: 500 }
    );
  }
};
