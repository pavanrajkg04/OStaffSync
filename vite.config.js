import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    allowedHosts: ["ostaffsync.onrender.com"],
    host: true, // allows external access (useful when deployed)
  },
});
