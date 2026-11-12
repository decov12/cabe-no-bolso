import { Outlet } from "react-router-dom";
import BarraTopo from "./BarraTopo";

// Moldura das telas que exigem login: barra do topo + a tela atual.
export default function LayoutLogado() {
  return (
    <>
      <BarraTopo />
      <main className="container py-5">
        <Outlet />
      </main>
    </>
  );
}
