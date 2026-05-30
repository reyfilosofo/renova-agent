import { NextRequest, NextResponse } from "next/server";
import { generateRenovaPlan } from "@/lib/agent";

export async function POST(request: NextRequest) {
  try {
    const body = (await request.json()) as { topic?: string; depth?: "brief" | "standard" | "doctoral" };

    if (!body.topic || body.topic.trim().length < 3) {
      return NextResponse.json({ error: "A topic with at least 3 characters is required." }, { status: 400 });
    }

    return NextResponse.json(
      generateRenovaPlan({
        topic: body.topic.trim(),
        depth: body.depth ?? "standard"
      })
    );
  } catch {
    return NextResponse.json({ error: "Invalid JSON payload." }, { status: 400 });
  }
}
