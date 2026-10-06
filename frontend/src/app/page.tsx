import { redirect } from "next/navigation";

/**
 * Root page — immediately redirects to /chat.
 * The redirect is also configured in next.config.ts for static builds.
 */
export default function HomePage() {
  redirect("/chat");
}
