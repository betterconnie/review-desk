// 審片網站的後台：每個審片台一份 JSON（意見、核准、開場選擇），存在 Netlify Blobs。
// GET /api/store?b=<board> -> 整份；POST {b, op:set|merge|del, c:集合, id, d} -> 改完的整份。單人使用，後寫的蓋掉先寫的。
import { getStore } from "@netlify/blobs";
const BOARD = /^[a-z0-9-]{1,40}$/, ID = /^[A-Za-z0-9_-]{1,40}$/, COLS = ["comments", "approvals", "choices", "meta"];
const json = (o, s = 200) => new Response(JSON.stringify(o), { status: s, headers: { "content-type": "application/json", "cache-control": "no-store" } });
export default async (req) => {
  const store = getStore({ name: "review", consistency: "strong" }), empty = () => ({ comments: {}, approvals: {}, choices: {}, meta: {} });
  if (req.method === "GET") {
    const b = new URL(req.url).searchParams.get("b") || ""; if (!BOARD.test(b)) return json({ error: "bad board" }, 400);
    return json((await store.get(b, { type: "json" })) || empty());
  }
  if (req.method !== "POST") return json({ error: "method" }, 405);
  let body; try { body = await req.json(); } catch { return json({ error: "json" }, 400); }
  const { b, op, c, id, d } = body || {};
  if (!BOARD.test(b || "") || !COLS.includes(c) || !ID.test(id || "")) return json({ error: "bad request" }, 400);
  if (d !== undefined && (typeof d !== "object" || d === null || JSON.stringify(d).length > 8000)) return json({ error: "bad data" }, 413);
  const doc = (await store.get(b, { type: "json" })) || empty(); doc[c] = doc[c] || {};
  if (op === "set") doc[c][id] = d;
  else if (op === "merge") { if (!doc[c][id]) return json({ error: "missing" }, 404); Object.assign(doc[c][id], d); }
  else if (op === "del") delete doc[c][id];
  else return json({ error: "op" }, 400);
  if (JSON.stringify(doc).length > 400000) return json({ error: "full" }, 413);   // 上限：防止被灌爆
  await store.setJSON(b, doc); return json(doc);
};
export const config = { path: "/api/store" };
