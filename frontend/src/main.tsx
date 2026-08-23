import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { ConfigProvider } from "antd";
import { Refine } from "@refinedev/core";
import { BrowserRouter } from "react-router";
import App from "./App";
import { AuthProvider } from "./context/AuthContext";
import "./styles.css";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <ConfigProvider theme={{
      token: {
        colorPrimary: "#ef3f25",
        colorText: "#1e2425",
        colorBgBase: "#fffaf3",
        borderRadius: 12,
        fontFamily: "'DM Sans', sans-serif",
      },
    }}>
      <BrowserRouter>
        <AuthProvider>
          <Refine options={{ syncWithLocation: true }}>
            <App />
          </Refine>
        </AuthProvider>
      </BrowserRouter>
    </ConfigProvider>
  </StrictMode>,
);

