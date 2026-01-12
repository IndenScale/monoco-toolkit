"use client";
import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { Spinner, Intent } from "@blueprintjs/core";

export default function Home() {
  const router = useRouter();

  useEffect(() => {
    router.push("/dashboard");
  }, [router]);

  return (
    <div className="flex h-screen items-center justify-center bg-canvas">
      <Spinner intent={Intent.PRIMARY} size={50} />
    </div>
  );
}
