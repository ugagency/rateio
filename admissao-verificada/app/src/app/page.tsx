import { redirect } from "next/navigation";

// A raiz leva ao painel; o middleware redireciona ao login se não houver sessão.
export default function Home() {
  redirect("/app/associados");
}
