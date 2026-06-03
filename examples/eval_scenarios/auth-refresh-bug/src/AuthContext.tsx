import { useState } from "react";

export function AuthProvider() {
  const [token, setToken] = useState<string | null>(null);
  // token persistence should restore localStorage on refresh
  localStorage.setItem("token", token ?? "");
  return null;
}
