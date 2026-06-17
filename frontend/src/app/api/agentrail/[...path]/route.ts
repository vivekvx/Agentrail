import { NextRequest, NextResponse } from "next/server";

const API_BASE_URL =
  process.env.AGENTRAIL_API_BASE_URL?.replace(/\/$/, "") ??
  process.env.DEVPILOT_API_BASE_URL?.replace(/\/$/, "") ??
  "http://127.0.0.1:8000/api";

export const dynamic = "force-dynamic";

// Only forward to known backend surfaces. Prevents the proxy from being used
// as an open relay to arbitrary backend paths.
const ALLOWED_PREFIXES = ["auth", "repos"];

async function proxyRequest(
  request: NextRequest,
  context: { params: Promise<{ path: string[] }> },
) {
  const { path } = await context.params;

  // Reject path traversal and anything outside the allowlisted surfaces.
  if (path.some((seg) => seg === "..") || !ALLOWED_PREFIXES.includes(path[0])) {
    return NextResponse.json({ detail: "Not found" }, { status: 404 });
  }

  const joinedPath = path.join("/");
  const targetUrl = new URL(`${API_BASE_URL}/${joinedPath}`);
  request.nextUrl.searchParams.forEach((value, key) => {
    targetUrl.searchParams.set(key, value);
  });

  const backendResponse = await fetch(targetUrl, {
    method: request.method,
    headers: {
      "Content-Type": request.headers.get("content-type") ?? "application/json",
    },
    body:
      request.method === "GET" || request.method === "HEAD"
        ? undefined
        : await request.text(),
    cache: "no-store",
  });

  return new NextResponse(await backendResponse.text(), {
    status: backendResponse.status,
    headers: {
      "Content-Type":
        backendResponse.headers.get("content-type") ?? "application/json",
    },
  });
}

export { proxyRequest as GET };
export { proxyRequest as POST };
export { proxyRequest as PUT };
export { proxyRequest as PATCH };
export { proxyRequest as DELETE };
